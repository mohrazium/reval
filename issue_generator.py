#!/usr/bin/env python3
"""
GitHub Issue Generator Script
تولید خودکار ایشوها از فایل Markdown roadmap
"""

import os
import re
import json
import argparse
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
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
    labels: Optional[List[str]] = None
    assignee: Optional[str] = None
    milestone: Optional[str] = None
    
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
    """GitHub Issue Generator از Markdown roadmap"""
    
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
        self.repo_owner = repo_owner
        
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
        current_day_range = None
        current_category = None
        current_tasks = []
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Phase detection (## 📋 Phase X: ...)
            phase_match = re.match(r'^##\s*📋\s*Phase\s*(\d+):\s*(.+?)\s*\((\d+)\s*weeks?\)', line, re.IGNORECASE)
            if phase_match:
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
                current_day_range = None
                current_category = None
                continue
            
            # Week detection (### Week X: ...)
            week_match = re.match(r'^###\s*Week\s*(\d+):\s*(.+)', line, re.IGNORECASE)
            if week_match:
                current_week = {
                    'number': int(week_match.group(1)),
                    'title': week_match.group(2).strip()
                }
                current_day_range = None
                current_category = None
                continue
            
            # Category/Day range detection (**Day X-Y: Category**)
            category_match = re.match(r'^\*\*Day\s*(\d+-\d+):\s*(.+)\*\*', line)
            if category_match and current_phase and current_week:
                current_day_range = category_match.group(1)
                current_category = category_match.group(2).strip()
                continue
            
            # Task detection (- [ ] ...)
            task_match = re.match(r'^-\s*\[\s*\]\s*(.+)', line)
            if task_match and current_phase and current_week and current_category:
                task_title = task_match.group(1).strip()
                
                priority = self._determine_task_priority(task_title)
                
                labels = [
                    f"week-{current_week['number']}",
                    current_category.lower().replace(' ', '-'),
                    priority
                ] + current_phase['labels']
                
                task = Task(
                    title=task_title,
                    description=self._generate_task_description(task_title, current_phase, current_week),
                    phase=current_phase['name'],
                    week=current_week['number'],
                    day_range=current_day_range or "",
                    category=current_category,
                    priority=priority,
                    labels=labels,
                    assignee=self.repo_owner,  # Set default assignee to repo owner
                    milestone=current_phase['name']
                )
                
                current_tasks.append(task)
        
        if current_phase:
            phases.append(Phase(
                name=current_phase['name'],
                description=current_phase['description'],
                duration_weeks=current_phase['duration'],
                tasks=current_tasks,
                labels=current_phase['labels']
            ))
        
        return phases
    
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
    
    def _generate_signature(self, task_title: str, phase_name: str, week_number: int) -> str:
        """Generate a unique signature for the task using hash"""
        unique_string = f"{phase_name}-{week_number}-{task_title}"
        return hashlib.md5(unique_string.encode('utf-8')).hexdigest()
    
    def _generate_task_description(self, task_title: str, phase: Dict, week: Dict) -> str:
        """Generate detailed task description with unique signature"""
        signature = self._generate_signature(task_title, phase['name'], week['number'])
        return f"""<!-- UNIQUE_SIGNATURE: {signature} -->

## Task Description
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

### Closing the Issue
- To close this issue, include one of these keywords in your commit message followed by the issue number:
  - `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves`, `resolved`
- Example: `git commit -m "Implement {task_title}, closes #<issue_number>"`
- Push to the default branch (e.g., main) to trigger automatic closure.

### Definition of Done
- ✅ Feature implemented according to requirements
- ✅ All tests passing
- ✅ Code reviewed and approved
- ✅ Documentation updated
- ✅ No critical bugs
        """
    
    def _split_task_into_subissues(self, task: Task) -> List[Task]:
        """Split a task into sub-issues based on complexity"""
        sub_tasks = []
        task_lower = task.title.lower()
        
        # Example: Split tasks related to authentication into smaller parts
        if 'auth' in task_lower or 'oauth2' in task_lower or 'jwt' in task_lower:
            sub_task_titles = [
                f"Implement OAuth2 setup for {task.title}",
                f"Add JWT handling for {task.title}",
                f"Integrate bcrypt password hashing for {task.title}",
                f"Write authentication tests for {task.title}"
            ]
            for i, sub_title in enumerate(sub_task_titles, 1):
                sub_task = Task(
                    title=f"{sub_title} (Sub-task {i}/{len(sub_task_titles)})",
                    description=self._generate_task_description(sub_title, 
                                                              {'name': task.phase, 'labels': task.labels}, 
                                                              {'number': task.week, 'title': f"Sub-task of Week {task.week}"}),
                    phase=task.phase,
                    week=task.week,
                    day_range=task.day_range,
                    category=task.category,
                    priority=task.priority,
                    labels=(task.labels or []) + ['sub-task'],
                    assignee=task.assignee,
                    milestone=task.milestone
                )
                sub_tasks.append(sub_task)
        else:
            # Default: Keep as single task
            sub_tasks.append(task)
        
        return sub_tasks
    
    def _issue_exists(self, signature: str) -> bool:
        """Check if an issue with the given signature already exists"""
        query = f"repo:{self.repo.full_name} is:issue \"{signature}\" in:body"
        try:
            issues = self.github.search_issues(query=query)
            return issues.totalCount > 0
        except GithubException as e:
            print(f"❌ Error searching for existing issue with signature {signature}: {e}")
            return False
    
    def save_parsed_to_file(self, phases: List[Phase], file_path: str) -> None:
        """Save parsed phases to JSON file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(phase) for phase in phases], f, indent=4, ensure_ascii=False)
        print(f"✅ Parsed data saved to: {file_path}")
    
    def load_parsed_from_file(self, file_path: str) -> List[Phase]:
        """Load parsed phases from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        phases = []
        for p_data in data:
            tasks = [Task(**t_data) for t_data in p_data['tasks']]
            phase = Phase(
                name=p_data['name'],
                description=p_data['description'],
                duration_weeks=p_data['duration_weeks'],
                tasks=tasks,
                labels=p_data['labels']
            )
            phases.append(phase)
        print(f"✅ Loaded parsed data from: {file_path}")
        return phases
    
    def create_labels(self, phases: List[Phase]) -> None:
        """Create GitHub labels for phases and categories"""
        standard_labels = [
            {"name": "high", "color": "d73a4a", "description": "High priority task"},
            {"name": "medium", "color": "fbca04", "description": "Medium priority task"},
            {"name": "low", "color": "0075ca", "description": "Low priority task"},
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
            {"name": "sub-task", "color": "00ccff", "description": "Sub-task of a larger issue"}
        ]
        
        for phase in phases:
            phase_match = re.search(r'Phase (\d+)', phase.name)
            phase_num = phase_match.group(1) if phase_match else "unknown"
            standard_labels.append({
                "name": f"phase-{phase_num}",
                "color": "b60205" if "Backend" in phase.name else "0e8a16",
                "description": f"{phase.name}"
            })
        
        week_colors = ["e4e669", "c7e9b4", "7fcdbb", "41b6c4", "1d91c0", 
                      "225ea8", "253494", "081d58", "f03b20", "bd0026"]
        for i in range(1, 11):
            standard_labels.append({
                "name": f"week-{i}",
                "color": week_colors[i-1] if i <= len(week_colors) else "cccccc",
                "description": f"Week {i} tasks"
            })
        
        existing_labels = {label.name for label in self.repo.get_labels()}
        for label_data in standard_labels:
            if label_data["name"] not in existing_labels:
                try:
                    self.repo.create_label(
                        name=label_data["name"],
                        color=label_data["color"],
                        description=label_data["description"]
                    )
                    print(f"✅ Created label: {label_data['name']}")
                except GithubException as e:
                    print(f"❌ Failed to create label {label_data['name']}: {e}")
            else:
                print(f"⏭️  Label already exists: {label_data['name']}")
    
    def create_milestones(self, phases: List[Phase]) -> Dict[str, Any]:
        """Create GitHub milestones for phases"""
        milestones = {}
        base_date = datetime.now()
        
        for i, phase in enumerate(phases):
            try:
                weeks_offset = sum(p.duration_weeks for p in phases[:i])
                due_date = base_date + timedelta(weeks=weeks_offset + phase.duration_weeks)
                
                milestone = self.repo.create_milestone(
                    title=phase.name,
                    description=phase.description,
                    due_on=due_date
                )
                milestones[phase.name] = milestone
                print(f"✅ Created milestone: {phase.name}")
                
            except GithubException as e:
                if "already_exists" in str(e):
                    for milestone in self.repo.get_milestones():
                        if milestone.title == phase.name:
                            milestones[phase.name] = milestone
                            print(f"⏭️  Milestone already exists: {phase.name}")
                            break
                else:
                    print(f"❌ Failed to create milestone {phase.name}: {e}")
        
        return milestones
    
    def _validate_assignee(self, assignee: str) -> bool:
        """Validate if the assignee is a collaborator in the repository"""
        try:
            collaborators = self.repo.get_collaborators()
            return any(collaborator.login == assignee for collaborator in collaborators)
        except GithubException as e:
            print(f"❌ Error validating assignee {assignee}: {e}")
            return False
    
    def create_issues(self, phases: List[Phase], milestones: Dict[str, Any], max_tasks: int) -> List[Dict[str, Any]]:
        """Create GitHub issues from tasks, splitting into sub-issues and checking duplicates"""
        created_issues = []
        skipped_issues = []
        task_count = 0
        
        for phase in phases:
            print(f"\n🚀 Processing issues for {phase.name}...")
            
            for task in phase.tasks:
                if task_count >= max_tasks:
                    print(f"⏹️ Reached maximum task limit ({max_tasks}). Stopping issue creation.")
                    break
                
                # Generate signature and check for duplicates
                signature = self._generate_signature(task.title, task.phase, task.week)
                if self._issue_exists(signature):
                    print(f"⏭️ Skipped duplicate issue: {task.title} (signature: {signature})")
                    skipped_issues.append(task.title)
                    continue
                
                # Split task into sub-issues if applicable
                tasks_to_create = self._split_task_into_subissues(task)
                task_count += 1
                
                for sub_task in tasks_to_create:
                    sub_signature = self._generate_signature(sub_task.title, sub_task.phase, sub_task.week)
                    if self._issue_exists(sub_signature):
                        print(f"⏭️ Skipped duplicate sub-issue: {sub_task.title} (signature: {sub_signature})")
                        skipped_issues.append(sub_task.title)
                        continue
                    
                    issue_kwargs = {}  # Initialize issue_kwargs to avoid unbound errors
                    try:
                        milestone = milestones.get(sub_task.milestone or "")
                        issue_kwargs = {
                            "title": sub_task.title,
                            "body": sub_task.description,
                            "labels": sub_task.labels or []
                        }
                        if milestone is not None:
                            issue_kwargs["milestone"] = milestone
                        
                        # Validate and assign assignee
                        if sub_task.assignee and self._validate_assignee(sub_task.assignee):
                            issue_kwargs["assignee"] = sub_task.assignee
                        else:
                            print(f"⚠️ Invalid or missing assignee {sub_task.assignee} for '{sub_task.title}'. Using repo owner {self.repo_owner}.")
                            issue_kwargs["assignee"] = self.repo_owner
                        
                        issue = self.repo.create_issue(**issue_kwargs)
                        
                        created_issues.append({
                            'number': issue.number,
                            'title': issue.title,
                            'url': issue.html_url,
                            'phase': sub_task.phase,
                            'week': sub_task.week
                        })
                        
                        print(f"✅ Created issue #{issue.number}: {sub_task.title} (signature: {sub_signature})")
                        
                    except GithubException as e:
                        print(f"❌ Failed to create issue '{sub_task.title}': {e}")
                        if "assignee" in str(e).lower():
                            print(f"⚠️ Assignee issue for '{sub_task.title}'. Retrying with repo owner {self.repo_owner}.")
                            issue_kwargs["assignee"] = self.repo_owner
                            try:
                                issue = self.repo.create_issue(**issue_kwargs)
                                created_issues.append({
                                    'number': issue.number,
                                    'title': issue.title,
                                    'url': issue.html_url,
                                    'phase': sub_task.phase,
                                    'week': sub_task.week
                                })
                                print(f"✅ Created issue #{issue.number}: {sub_task.title} (with repo owner)")
                            except GithubException as retry_e:
                                print(f"❌ Retry failed for '{sub_task.title}': {retry_e}")
        
        print(f"\n📊 Issues Summary: Created {len(created_issues)}, Skipped {len(skipped_issues)} duplicates")
        return created_issues
    
    def generate_summary_report(self, phases: List[Phase], created_issues: List[Dict[str, Any]]) -> str:
        """Generate summary report of created issues"""
        report = f"""# GitHub Issues Creation Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Repository:** {self.repo.full_name}

## Summary
- **Total Phases:** {len(phases)}
- **Total Tasks Processed:** {sum(len(phase.tasks) for phase in phases)}
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
    parser.add_argument('--file', help='Path to markdown roadmap file')
    parser.add_argument('--output', help='Output file for summary report')
    parser.add_argument('--dry-run', action='store_true', help='Parse only, do not create issues')
    parser.add_argument('--from-parsed', help='Load parsed phases from JSON file instead of parsing MD')
    
    args = parser.parse_args()
    
    try:
        repo_owner, repo_name = args.repo.split('/')
    except ValueError:
        print("❌ Repository format should be: owner/repo-name")
        return
    
    generator = GitHubIssueGenerator(args.token, repo_owner, repo_name)
    print(f"🚀 Connected to repository: {args.repo}")
    
    try:
        if args.from_parsed:
            if not Path(args.from_parsed).exists():
                print(f"❌ File not found: {args.from_parsed}")
                return
            phases = generator.load_parsed_from_file(args.from_parsed)
        else:
            if not args.file or not Path(args.file).exists():
                print(f"❌ File not found: {args.file}")
                return
            print("📖 Parsing roadmap...")
            phases = generator.parse_markdown_roadmap(args.file)
            print(f"✅ Found {len(phases)} phases with {sum(len(p.tasks) for p in phases)} tasks")
            
            save_response = input("Do you want to save the parsed data in JSON? (y/n): ").strip().lower()
            if save_response == 'y':
                save_file = input("Enter filename to save (default: parsed_phases.json): ").strip() or 'parsed_phases.json'
                generator.save_parsed_to_file(phases, save_file)
        
        total_tasks = sum(len(phase.tasks) for phase in phases)
        if args.dry_run:
            print("\n🔍 DRY RUN - No issues will be created")
            for phase in phases:
                print(f"\nPhase: {phase.name}")
                print(f"Tasks: {len(phase.tasks)}")
                for task in phase.tasks[:3]:
                    print(f"  - {task.title}")
                if len(phase.tasks) > 3:
                    print(f"  ... and {len(phase.tasks) - 3} more tasks")
            return
        
        # Prompt for number of tasks to convert to issues
        max_tasks = total_tasks
        prompt = f"You have {total_tasks} tasks and you want how many tasks put into GitHub as issues? (1-{total_tasks}, default {total_tasks}): "
        try:
            task_limit = input(prompt).strip()
            max_tasks = int(task_limit) if task_limit else total_tasks
            if max_tasks < 1 or max_tasks > total_tasks:
                raise ValueError
        except ValueError:
            print(f"❌ Invalid input. Using default: {total_tasks} tasks")
            max_tasks = total_tasks
        
        create_response = input("Do you want to create issues in GitHub? (y/n): ").strip().lower()
        if create_response != 'y':
            print("❌ Aborting issue creation.")
            return
        
        print("\n🏷️  Creating labels...")
        generator.create_labels(phases)
        
        print("\n🎯 Creating milestones...")
        milestones = generator.create_milestones(phases)
        
        print("\n📝 Creating issues...")
        created_issues = generator.create_issues(phases, milestones, max_tasks)
        
        report = generator.generate_summary_report(phases, created_issues)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📊 Report saved to: {args.output}")
        else:
            print("\n" + "="*50)
            print(report)
        
        print(f"\n🎉 Successfully created {len(created_issues)} issues!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

# Usage : python issue_generator.py --token TOKEN --repo user/repo --file github_issue_gen/roadmap.md --output res.md
if __name__ == "__main__":
    main()
