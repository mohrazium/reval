# Smart Task Manager - Flutter with MobX Setup Guide

## شروع پروژه - Step by Step

### **Day 1-2: Project Structure**

#### **1. Git Repository Setup:**
```bash
# روی local machine:
mkdir smart-task-manager
cd smart-task-manager

# Structure کلی:
smart-task-manager/
├── backend/          # FastAPI
├── mobile/           # Flutter
├── docker-compose.yml
├── README.md
└── .gitignore
```

#### **2. Backend Setup (FastAPI):**
```bash
cd backend
mkdir app tests

# Structure:
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   ├── api/
│   ├── core/
│   └── db/
├── requirements.txt
├── Dockerfile
└── .env.example
```

#### **3. Flutter Setup:**
```bash
cd ../
flutter create mobile
cd mobile

# Clean کن default code
# Structure تغییر بده به feature-based
```

---

## Week 1: Backend Foundation

### **Day 1: FastAPI Basic Setup**

#### **requirements.txt:**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.7
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pydantic-settings==2.0.3
```

#### **main.py (ساده):**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Smart Task Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Smart Task Manager API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### **Day 2-3: Database Models**

#### **models/user.py:**
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### **models/task.py:**
```python
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(String, default="todo")  # todo, in_progress, completed
    priority = Column(String, default="medium")  # low, medium, high
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
```

### **Day 4-5: Authentication**

#### **auth.py:**
```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

---

## Week 2: Flutter Foundation with MobX

### **Day 1-2: Project Structure**
```dart
lib/
├── main.dart
├── core/
│   ├── constants/
│   ├── utils/
│   ├── services/
│   └── di/              # Dependency Injection
├── features/
│   ├── auth/
│   │   ├── data/
│   │   ├── domain/
│   │   ├── presentation/
│   │   │   ├── stores/   # MobX Stores
│   │   │   ├── screens/
│   │   │   └── widgets/
│   ├── tasks/
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │       ├── stores/   # MobX Stores
│   │       ├── screens/
│   │       └── widgets/
│   └── dashboard/
├── shared/
│   ├── widgets/
│   ├── models/
│   └── stores/          # Global MobX Stores
└── config/
```

### **Day 3: Dependencies Setup**

#### **pubspec.yaml:**
```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # State Management (MobX)
  mobx: ^2.3.0+1
  flutter_mobx: ^2.2.0+2
  
  # HTTP & API
  dio: ^5.3.2
  retrofit: ^4.0.3
  json_annotation: ^4.8.1
  
  # Navigation
  go_router: ^12.1.1
  
  # Storage
  shared_preferences: ^2.2.2
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  
  # UI & Utils
  get_it: ^7.6.4
  injectable: ^2.3.2
  
dev_dependencies:
  flutter_test:
    sdk: flutter
  
  # Code Generation
  build_runner: ^2.4.7
  mobx_codegen: ^2.4.0
  retrofit_generator: ^8.0.4
  json_serializable: ^6.7.1
  injectable_generator: ^2.4.1
  hive_generator: ^2.0.1
```

### **Day 4: MobX Store Setup**

#### **shared/stores/app_store.dart:**
```dart
import 'package:mobx/mobx.dart';

part 'app_store.g.dart';

class AppStore = _AppStore with _$AppStore;

abstract class _AppStore with Store {
  @observable
  bool isLoading = false;

  @observable
  String? errorMessage;

  @observable
  bool isDarkMode = false;

  @action
  void setLoading(bool loading) {
    isLoading = loading;
  }

  @action
  void setError(String? error) {
    errorMessage = error;
  }

  @action
  void toggleTheme() {
    isDarkMode = !isDarkMode;
  }

  @action
  void clearError() {
    errorMessage = null;
  }
}
```

#### **features/auth/presentation/stores/auth_store.dart:**
```dart
import 'package:mobx/mobx.dart';
import '../../../domain/entities/user.dart';
import '../../../domain/usecases/login_usecase.dart';
import '../../../domain/usecases/register_usecase.dart';

part 'auth_store.g.dart';

class AuthStore = _AuthStore with _$AuthStore;

abstract class _AuthStore with Store {
  final LoginUseCase _loginUseCase;
  final RegisterUseCase _registerUseCase;

  _AuthStore(this._loginUseCase, this._registerUseCase);

  @observable
  User? currentUser;

  @observable
  bool isAuthenticated = false;

  @observable
  bool isLoading = false;

  @observable
  String? errorMessage;

  @action
  Future<void> login(String email, String password) async {
    setLoading(true);
    clearError();

    try {
      final user = await _loginUseCase.execute(email, password);
      currentUser = user;
      isAuthenticated = true;
    } catch (e) {
      errorMessage = e.toString();
    } finally {
      setLoading(false);
    }
  }

  @action
  Future<void> register(String username, String email, String password) async {
    setLoading(true);
    clearError();

    try {
      final user = await _registerUseCase.execute(username, email, password);
      currentUser = user;
      isAuthenticated = true;
    } catch (e) {
      errorMessage = e.toString();
    } finally {
      setLoading(false);
    }
  }

  @action
  void logout() {
    currentUser = null;
    isAuthenticated = false;
    clearError();
  }

  @action
  void setLoading(bool loading) {
    isLoading = loading;
  }

  @action
  void clearError() {
    errorMessage = null;
  }
}
```

#### **features/tasks/presentation/stores/task_store.dart:**
```dart
import 'package:mobx/mobx.dart';
import '../../../domain/entities/task.dart';
import '../../../domain/usecases/get_tasks_usecase.dart';
import '../../../domain/usecases/create_task_usecase.dart';
import '../../../domain/usecases/update_task_usecase.dart';
import '../../../domain/usecases/delete_task_usecase.dart';

part 'task_store.g.dart';

class TaskStore = _TaskStore with _$TaskStore;

abstract class _TaskStore with Store {
  final GetTasksUseCase _getTasksUseCase;
  final CreateTaskUseCase _createTaskUseCase;
  final UpdateTaskUseCase _updateTaskUseCase;
  final DeleteTaskUseCase _deleteTaskUseCase;

  _TaskStore(
    this._getTasksUseCase,
    this._createTaskUseCase,
    this._updateTaskUseCase,
    this._deleteTaskUseCase,
  );

  @observable
  ObservableList<Task> tasks = ObservableList<Task>();

  @observable
  bool isLoading = false;

  @observable
  String? errorMessage;

  @observable
  String selectedFilter = 'all'; // all, todo, in_progress, completed

  @computed
  List<Task> get filteredTasks {
    if (selectedFilter == 'all') return tasks;
    return tasks.where((task) => task.status == selectedFilter).toList();
  }

  @computed
  int get completedTasksCount {
    return tasks.where((task) => task.status == 'completed').length;
  }

  @computed
  int get pendingTasksCount {
    return tasks.where((task) => task.status != 'completed').length;
  }

  @action
  Future<void> loadTasks() async {
    setLoading(true);
    clearError();

    try {
      final taskList = await _getTasksUseCase.execute();
      tasks.clear();
      tasks.addAll(taskList);
    } catch (e) {
      errorMessage = e.toString();
    } finally {
      setLoading(false);
    }
  }

  @action
  Future<void> createTask(Task task) async {
    setLoading(true);
    clearError();

    try {
      final newTask = await _createTaskUseCase.execute(task);
      tasks.add(newTask);
    } catch (e) {
      errorMessage = e.toString();
    } finally {
      setLoading(false);
    }
  }

  @action
  Future<void> updateTask(Task task) async {
    try {
      final updatedTask = await _updateTaskUseCase.execute(task);
      final index = tasks.indexWhere((t) => t.id == task.id);
      if (index != -1) {
        tasks[index] = updatedTask;
      }
    } catch (e) {
      errorMessage = e.toString();
    }
  }

  @action
  Future<void> deleteTask(int taskId) async {
    try {
      await _deleteTaskUseCase.execute(taskId);
      tasks.removeWhere((task) => task.id == taskId);
    } catch (e) {
      errorMessage = e.toString();
    }
  }

  @action
  void setFilter(String filter) {
    selectedFilter = filter;
  }

  @action
  void setLoading(bool loading) {
    isLoading = loading;
  }

  @action
  void clearError() {
    errorMessage = null;
  }
}
```

### **Day 5: Dependency Injection Setup**

#### **core/di/injection.dart:**
```dart
import 'package:get_it/get_it.dart';
import 'package:injectable/injectable.dart';
import '../../features/auth/presentation/stores/auth_store.dart';
import '../../features/tasks/presentation/stores/task_store.dart';
import '../../shared/stores/app_store.dart';

import 'injection.config.dart';

final getIt = GetIt.instance;

@InjectableInit()
void configureDependencies() => getIt.init();

void setupStores() {
  // Register Stores
  getIt.registerLazySingleton<AppStore>(() => AppStore());
  getIt.registerLazySingleton<AuthStore>(() => AuthStore(
    getIt<LoginUseCase>(),
    getIt<RegisterUseCase>(),
  ));
  getIt.registerLazySingleton<TaskStore>(() => TaskStore(
    getIt<GetTasksUseCase>(),
    getIt<CreateTaskUseCase>(),
    getIt<UpdateTaskUseCase>(),
    getIt<DeleteTaskUseCase>(),
  ));
}
```

---

## Week 3: Core Features

### **Backend: Task CRUD APIs**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

router = APIRouter()

@router.post("/tasks/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_task = Task(**task.dict(), user_id=current_user.id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks/", response_model=List[TaskResponse])
async def get_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    return tasks

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int, 
    task: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_task = db.query(Task).filter(
        Task.id == task_id, 
        Task.user_id == current_user.id
    ).first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    for field, value in task.dict(exclude_unset=True).items():
        setattr(db_task, field, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_task = db.query(Task).filter(
        Task.id == task_id, 
        Task.user_id == current_user.id
    ).first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}
```

### **Flutter: MobX Reactive UI**

#### **features/tasks/presentation/screens/task_list_screen.dart:**
```dart
import 'package:flutter/material.dart';
import 'package:flutter_mobx/flutter_mobx.dart';
import 'package:get_it/get_it.dart';
import '../stores/task_store.dart';
import '../widgets/task_item.dart';

class TaskListScreen extends StatefulWidget {
  @override
  _TaskListScreenState createState() => _TaskListScreenState();
}

class _TaskListScreenState extends State<TaskListScreen> {
  final TaskStore _taskStore = GetIt.instance<TaskStore>();

  @override
  void initState() {
    super.initState();
    _taskStore.loadTasks();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Tasks'),
        actions: [
          Observer(
            builder: (_) => Chip(
              label: Text('${_taskStore.completedTasksCount}/${_taskStore.tasks.length}'),
              backgroundColor: Colors.green.shade100,
            ),
          ),
          SizedBox(width: 16),
        ],
      ),
      body: Column(
        children: [
          // Filter Tabs
          Container(
            height: 50,
            child: Observer(
              builder: (_) => ListView(
                scrollDirection: Axis.horizontal,
                children: [
                  _buildFilterChip('all', 'همه'),
                  _buildFilterChip('todo', 'انجام نشده'),
                  _buildFilterChip('in_progress', 'در حال انجام'),
                  _buildFilterChip('completed', 'تکمیل شده'),
                ],
              ),
            ),
          ),
          
          // Tasks List
          Expanded(
            child: Observer(
              builder: (_) {
                if (_taskStore.isLoading) {
                  return Center(child: CircularProgressIndicator());
                }

                if (_taskStore.errorMessage != null) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.error, size: 64, color: Colors.red),
                        SizedBox(height: 16),
                        Text(_taskStore.errorMessage!),
                        ElevatedButton(
                          onPressed: () => _taskStore.loadTasks(),
                          child: Text('تلاش مجدد'),
                        ),
                      ],
                    ),
                  );
                }

                if (_taskStore.filteredTasks.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.task_alt, size: 64, color: Colors.grey),
                        SizedBox(height: 16),
                        Text('هیچ تسکی وجود ندارد'),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  itemCount: _taskStore.filteredTasks.length,
                  itemBuilder: (context, index) {
                    final task = _taskStore.filteredTasks[index];
                    return TaskItem(
                      task: task,
                      onStatusChanged: (newStatus) {
                        final updatedTask = task.copyWith(status: newStatus);
                        _taskStore.updateTask(updatedTask);
                      },
                      onDelete: () => _taskStore.deleteTask(task.id),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddTaskDialog(),
        child: Icon(Icons.add),
      ),
    );
  }

  Widget _buildFilterChip(String filter, String label) {
    return Observer(
      builder: (_) => Padding(
        padding: EdgeInsets.symmetric(horizontal: 4),
        child: FilterChip(
          label: Text(label),
          selected: _taskStore.selectedFilter == filter,
          onSelected: (selected) {
            if (selected) _taskStore.setFilter(filter);
          },
        ),
      ),
    );
  }

  void _showAddTaskDialog() {
    // Navigate to Add Task Screen or show Dialog
  }
}
```

#### **features/tasks/presentation/widgets/task_item.dart:**
```dart
import 'package:flutter/material.dart';
import '../../domain/entities/task.dart';

class TaskItem extends StatelessWidget {
  final Task task;
  final Function(String) onStatusChanged;
  final VoidCallback onDelete;

  const TaskItem({
    Key? key,
    required this.task,
    required this.onStatusChanged,
    required this.onDelete,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: ListTile(
        leading: _buildStatusIcon(),
        title: Text(
          task.title,
          style: TextStyle(
            decoration: task.status == 'completed' 
                ? TextDecoration.lineThrough 
                : null,
          ),
        ),
        subtitle: task.description != null 
            ? Text(task.description!) 
            : null,
        trailing: PopupMenuButton<String>(
          onSelected: (value) {
            switch (value) {
              case 'todo':
              case 'in_progress':
              case 'completed':
                onStatusChanged(value);
                break;
              case 'delete':
                onDelete();
                break;
            }
          },
          itemBuilder: (context) => [
            PopupMenuItem(value: 'todo', child: Text('انجام نشده')),
            PopupMenuItem(value: 'in_progress', child: Text('در حال انجام')),
            PopupMenuItem(value: 'completed', child: Text('تکمیل شده')),
            PopupMenuDivider(),
            PopupMenuItem(
              value: 'delete',
              child: Text('حذف', style: TextStyle(color: Colors.red)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusIcon() {
    switch (task.status) {
      case 'completed':
        return Icon(Icons.check_circle, color: Colors.green);
      case 'in_progress':
        return Icon(Icons.access_time, color: Colors.orange);
      default:
        return Icon(Icons.radio_button_unchecked, color: Colors.grey);
    }
  }
}
```

---

## Code Generation Commands

### **هر بار که Store تغییر کردی:**
```bash
# Run code generation
flutter packages pub run build_runner build

# Watch for changes (during development)
flutter packages pub run build_runner watch

# Clean and rebuild
flutter packages pub run build_runner clean
flutter packages pub run build_runner build --delete-conflicting-outputs
```

---

## أولویت‌بندی Development:

### **هفته 1: Backend API** ⚡
- User registration/login
- Basic task CRUD
- Database setup

### **هفته 2: Flutter MobX Setup** 📱
- MobX stores setup
- Authentication flow
- HTTP client with Dio/Retrofit

### **هفته 3: Core MVP** 🎯
- Task management UI با MobX reactivity
- API integration
- Local storage with Hive

### **هفته 4: Polish MVP** ✨
- Bug fixes
- UI improvements
- Basic notifications

---

## نکات مهم MobX:

### **Best Practices:**
1. **Small Stores:** هر feature یک store داشته باشه
2. **Computed Values:** برای derived state استفاده کن
3. **Actions:** همه state changes در actions باشه
4. **Observer:** فقط جاهایی که state تغییر می‌کنه wrap کن
5. **Reactions:** برای side effects استفاده کن

### **Performance Tips:**
- Observer رو دقیقاً روی widget هایی که تغییر می‌کنن بذار
- Computed values رو cache می‌کنه، زیاد استفاده کن
- Store ها رو singleton کن با GetIt

### **Development Workflow:**
1. Store بنویس
2. Code generation اجرا کن
3. UI با Observer wrap کن
4. Test reactivity

**آماده‌ای شروع کنیم؟** کدوم قسمت رو اول می‌خوای tackle کنیم؟ 🚀
