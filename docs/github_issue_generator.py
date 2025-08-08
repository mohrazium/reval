#!/usr/bin/env python3
"""
GitHub Issue Generator Script
ØªÙˆÙ„ÛŒØ¯ Ø®ÙˆØ¯Ú©Ø§Ø± Ø§ÛŒØ´ÙˆÙ‡Ø§ Ø§Ø² ÙØ§ÛŒÙ„ Markdown roadmap
"""

import os
import re
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import requests
from github import Github
from github.GithubException import GithubException


@dataclass
class Task:
    """Task data structure"""
    title: str
    description: str
    phase: str
    week: int
    day_range: str
    category: str
    priority: str = "medium"
    labels: List[str] = None
    assignee: str = None
    milestone: str = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []


@dataclass
class Phase:
    """Phase data structure"""
    name: str
    description: str
    duration_weeks: int
    tasks: List[Task]
    labels: List[str]


class GitHubIssueGenerator:
    """GitHub Issue Generator Ø§Ø² Markdown roadmap"""
    
    def __init__(self, token: str, repo_owner: str, repo_name: str):
        """
        Initialize GitHub client
        
        Args:
            token: GitHub personal access token
            repo_owner: Repository owner username
            repo_name: Repository name
        """
        self.github = Github(token)
        self.repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
        self.token = token
        
    def parse_markdown_roadmap(self, file_path: str) -> List[Phase]:
        """
        Parse markdown roadmap file and extract phases and tasks
        
        Args:
            file_path: Path to markdown roadmap file
            
        Returns:
            List of Phase objects
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        phases = []
        current_phase = None
        current_week = None
        current_tasks = []
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Phase detection (## ðŸ“‹ Phase X: ...)
            phase_match = re.match(r'^##\s*ðŸ“‹\s*Phase\s*(\d+):\s*(.+)\s*\((\d+)-?(\d+)?\s*weeks?\)', line, re.IGNORECASE)
            if phase_match:
                # Save previous phase
                if current_phase:
                    phases.append(Phase(
                        name=current_phase['name'],
                        description=current_phase['description'],
                        duration_weeks=current_phase['duration'],
                        tasks=current_tasks,
                        labels=current_phase['labels']
                    ))
                
                phase_num = phase_match.group(1)
                phase_name = phase_match.group(2).strip()
                duration = int(phase_match.group(3))
                
                current_phase = {
                    'name': f"Phase {phase_num}: {phase_name}",
                    'description': f"Phase {phase_num} - {phase_name}",
                    'duration': duration,
                    'labels': [f"phase-{phase_num}", "backend" if "Backend" in phase_name else "frontend"]
                }
                current_tasks = []
                continue
            
            # Week detection (### Week X: ...)
            week_match = re.match(r'^###\s*Week\s*(\d+):\s*(.+)', line, re.IGNORECASE)
            if week_match:
                current_week = {
                    'number': int(week_match.group(1)),
                    'title': week_match.group(2).strip()
                }
                continue
            
            # Task detection (- [ ] ...)
            task_match = re.match(r'^-\s*\[\s*\]\s*(.+)', line)
            if task_match and current_phase and current_week:
                task_title = task_match.group(1).strip()
                
                # Determine category based on content
                category = self._determine_task_category(task_title)
                
                # Determine priority based on keywords
                priority = self._determine_task_priority(task_title)
                
                # Create labels
                labels = [
                    f"week-{current_week['number']}",
                    category,
                    priority
                ] + current_phase['labels']
                
                task = Task(
                    title=task_title,
                    description=self._generate_task_description(task_title, current_phase, current_week),
                    phase=current_phase['name'],
                    week=current_week['number'],
                    day_range="",
                    category=category,
                    priority=priority,
                    labels=labels,
                    milestone=current_phase['name']
                )
                
                current_tasks.append(task)
        
        # Add last phase
        if current_phase:
            phases.append(Phase(
                name=current_phase['name'],
                description=current_phase['description'],
                duration_weeks=current_phase['duration'],
                tasks=current_tasks,
                labels=current_phase['labels']
            ))
        
        return phases
    
    def _determine_task_category(self, task_title: str) -> str:
        """Determine task category based on title content"""
        task_lower = task_title.lower()
        
        if any(word in task_lower for word in ['test', 'unit', 'integration', 'coverage']):
            return 'testing'
        elif any(word in task_lower for word in ['ui', 'screen', 'widget', 'design']):
            return 'ui-ux'
        elif any(word in task_lower for word in ['api', 'endpoint', 'route']):
            return 'api'
        elif any(word in task_lower for word in ['database', 'migration', 'model', 'schema']):
            return 'database'
        elif any(word in task_lower for word in ['auth', 'login', 'token', 'jwt']):
            return 'authentication'
        elif any(word in task_lower for word in ['ai', 'openai', 'suggestion', 'intelligent']):
            return 'ai-integration'
        elif any(word in task_lower for word in ['docker', 'deploy', 'ci/cd', 'pipeline']):
            return 'devops'
        elif any(word in task_lower for word in ['github', 'obsidian', 'external', 'integration']):
            return 'integration'
        else:
            return 'development'
    
    def _determine_task_priority(self, task_title: str) -> str:
        """Determine task priority based on title content"""
        task_lower = task_title.lower()
        
        if any(word in task_lower for word in ['critical', 'urgent', 'security', 'auth']):
            return 'high'
        elif any(word in task_lower for word in ['optimization', 'performance', 'advanced']):
            return 'medium'
        elif any(word in task_lower for word in ['documentation', 'comment', 'polish']):
            return 'low'
        else:
            return 'medium'
    
    def _generate_task_description(self, task_title: str, phase: Dict, week: Dict) -> str:
        """Generate detailed task description"""
        return f"""## Task Description
**Phase:** {phase['name']}
**Week:** Week {week['number']} - {week['title']}

### Task Details
{task_title}

### Acceptance Criteria
- [ ] Code implementation completed
- [ ] Unit tests written (>80% coverage)
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Integration tests passed

### Technical Notes
- Follow Clean Architecture principles
- Implement proper error handling
- Add comprehensive logging
- Ensure security best practices

### Definition of Done
- âœ… Feature implemented according to requirements
- âœ… All tests passing
- âœ… Code reviewed and approved
- âœ… Documentation updated
- âœ… No critical bugs
        """
    
    def create_labels(self, phases: List[Phase]) -> None:
        """Create GitHub labels for phases and categories"""
        
        # Standard labels
        standard_labels = [
            # Priority labels
            {"name": "high", "color": "d73a4a", "description": "High priority task"},
            {"name": "medium", "color": "fbca04", "description": "Medium priority task"},
            {"name": "low", "color": "0075ca", "description": "Low priority task"},
            
            # Category labels
            {"name": "backend", "color": "1d76db", "description": "Backend development"},
            {"name": "frontend", "color": "0e8a16", "description": "Frontend development"},
            {"name": "testing", "color": "5319e7", "description": "Testing related tasks"},
            {"name": "ui-ux", "color": "f9d0c4", "description": "UI/UX design and implementation"},
            {"name": "api", "color": "c2e0c6", "description": "API development"},
            {"name": "database", "color": "fef2c0", "description": "Database related tasks"},
            {"name": "authentication", "color": "d4c5f9", "description": "Authentication and security"},
            {"name": "ai-integration", "color": "ff6b6b", "description": "AI and machine learning"},
            {"name": "devops", "color": "bfd4f2", "description": "DevOps and deployment"},
            {"name": "integration", "color": "c5def5", "description": "External integrations"},
            {"name": "development", "color": "7057ff", "description": "General development"},
            {"name": "documentation", "color": "0052cc", "description": "Documentation tasks"},
        ]
        
        # Phase labels
        for phase in phases:
            phase_num = re.search(r'Phase (\d+)', phase.name).group(1)
            standard_labels.append({
                "name": f"phase-{phase_num}",
                "color": "b60205" if "Backend" in phase.name else "0e8a16",
                "description": f"{phase.name}"
            })
        
        # Week labels (1-10)
        week_colors = ["e4e669", "c7e9b4", "7fcdbb", "41b6c4", "1d91c0", 
                      "225ea8", "253494", "081d58", "f03b20", "bd0026"]
        
        for i in range(1, 11):
            standard_labels.append({
                "name": f"week-{i}",
                "color": week_colors[i-1] if i <= len(week_colors) else "cccccc",
                "description": f"Week {i} tasks"
            })
        
        # Create labels
        existing_labels = {label.name for label in self.repo.get_labels()}
        
        for label_data in standard_labels:
            if label_data["name"] not in existing_labels:
                try:
                    self.repo.create_label(
                        name=label_data["name"],
                        color=label_data["color"],
                        description=label_data["description"]
                    )
                    print(f"âœ… Created label: {label_data['name']}")
                except GithubException as e:
                    print(f"âŒ Failed to create label {label_data['name']}: {e}")
            else:
                print(f"â­ï¸  Label already exists: {label_data['name']}")
    
    def create_milestones(self, phases: List[Phase]) -> Dict[str, Any]:
        """Create GitHub milestones for phases"""
        milestones = {}
        base_date = datetime.now()
        
        for i, phase in enumerate(phases):
            try:
                # Calculate due date
                weeks_offset = sum(p.duration_weeks for p in phases[:i])
                due_date = base_date + timedelta(weeks=weeks_offset + phase.duration_weeks)
                
                milestone = self.repo.create_milestone(
                    title=phase.name,
                    description=phase.description,
                    due_on=due_date
                )
                milestones[phase.name] = milestone
                print(f"âœ… Created milestone: {phase.name}")
                
            except GithubException as e:
                if "already_exists" in str(e):
                    # Get existing milestone
                    for milestone in self.repo.get_milestones():
                        if milestone.title == phase.name:
                            milestones[phase.name] = milestone
                            print(f"â­ï¸  Milestone already exists: {phase.name}")
                            break
                else:
                    print(f"âŒ Failed to create milestone {phase.name}: {e}")
        
        return milestones
    
    def create_issues(self, phases: List[Phase], milestones: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create GitHub issues from tasks"""
        created_issues = []
        
        for phase in phases:
            print(f"\nðŸš€ Creating issues for {phase.name}...")
            
            for task in phase.tasks:
                try:
                    # Get milestone
                    milestone = milestones.get(task.milestone)
                    
                    # Create issue
                    issue = self.repo.create_issue(
                        title=task.title,
                        body=task.description,
                        labels=task.labels,
                        milestone=milestone,
                        assignee=task.assignee
                    )
                    
                    created_issues.append({
                        'number': issue.number,
                        'title': issue.title,
                        'url': issue.html_url,
                        'phase': task.phase,
                        'week': task.week
                    })
                    
                    print(f"âœ… Created issue #{issue.number}: {task.title}")
                    
                except GithubException as e:
                    print(f"âŒ Failed to create issue '{task.title}': {e}")
        
        return created_issues
    
    def generate_summary_report(self, phases: List[Phase], created_issues: List[Dict[str, Any]]) -> str:
        """Generate summary report of created issues"""
        report = f"""# GitHub Issues Creation Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Repository:** {self.repo.full_name}

## Summary
- **Total Phases:** {len(phases)}
- **Total Tasks:** {sum(len(phase.tasks) for phase in phases)}
- **Created Issues:** {len(created_issues)}

## Created Issues by Phase

"""
        
        for phase in phases:
            phase_issues = [issue for issue in created_issues if issue['phase'] == phase.name]
            report += f"### {phase.name}\n"
            report += f"**Issues Created:** {len(phase_issues)}\n\n"
            
            for issue in phase_issues:
                report += f"- [#{issue['number']}]({issue['url']}) {issue['title']} (Week {issue['week']})\n"
            
            report += "\n"
        
        return report


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate GitHub issues from Markdown roadmap')
    parser.add_argument('--token', required=True, help='GitHub personal access token')
    parser.add_argument('--repo', required=True, help='Repository in format owner/repo-name')
    parser.add_argument('--file', required=True, help='Path to markdown roadmap file')
    parser.add_argument('--output', help='Output file for summary report')
    parser.add_argument('--dry-run', action='store_true', help='Parse only, do not create issues')
    
    args = parser.parse_args()
    
    # Parse repository
    try:
        repo_owner, repo_name = args.repo.split('/')
    except ValueError:
        print("âŒ Repository format should be: owner/repo-name")
        return
    
    # Check if file exists
    if not Path(args.file).exists():
        print(f"âŒ File not found: {args.file}")
        return
    
    try:
        # Initialize generator
        generator = GitHubIssueGenerator(args.token, repo_owner, repo_name)
        print(f"ðŸš€ Connected to repository: {args.repo}")
        
        # Parse roadmap
        print("ðŸ“– Parsing roadmap...")
        phases = generator.parse_markdown_roadmap(args.file)
        print(f"âœ… Found {len(phases)} phases with {sum(len(p.tasks) for p in phases)} tasks")
        
        if args.dry_run:
            print("\nðŸ” DRY RUN - No issues will be created")
            for phase in phases:
                print(f"\nPhase: {phase.name}")
                print(f"Tasks: {len(phase.tasks)}")
                for task in phase.tasks[:3]:  # Show first 3 tasks
                    print(f"  - {task.title}")
                if len(phase.tasks) > 3:
                    print(f"  ... and {len(phase.tasks) - 3} more tasks")
            return
        
        # Create labels
        print("\nðŸ·ï¸  Creating labels...")
        generator.create_labels(phases)
        
        # Create milestones
        print("\nðŸŽ¯ Creating milestones...")
        milestones = generator.create_milestones(phases)
        
        # Create issues
        print("\nðŸ“ Creating issues...")
        created_issues = generator.create_issues(phases, milestones)
        
        # Generate report
        report = generator.generate_summary_report(phases, created_issues)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"ðŸ“Š Report saved to: {args.output}")
        else:
            print("\n" + "="*50)
            print(report)
        
        print(f"\nðŸŽ‰ Successfully created {len(created_issues)} issues!")
        
    except Exception as e:
        print(f"âŒ Error: {e}")
        raise


if __name__ == "__main__":
    main()