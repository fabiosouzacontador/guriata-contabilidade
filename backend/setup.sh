#!/bin/bash
# Setup script for Guriata Contabilidade SaaS FastAPI application

# Function to print messages
print_message() {
    echo "\033[1;32m"$1"\033[0m"
}

# Create directory structure
print_message "Creating directory structure..."
mkdir -p app/core app/models app/schemas app/routers

# Create __init__.py files
print_message "Creating __init__.py files..."
touch app/core/__init__.py app/models/__init__.py app/schemas/__init__.py app/routers/__init__.py

# Create and populate app/core/config.py
print_message "Creating app/core/config.py..."
echo "# Configuration settings\n\nAPI_TITLE = 'Guriata Contabilidade'\nAPI_VERSION = '1.0'\n\nDATABASE_URL = 'sqlite:///./test.db'" > app/core/config.py

# Create and populate app/core/security.py
print_message "Creating app/core/security.py..."
echo "from passlib.context import CryptContext\nfrom jose import JWTError, jwt\n\nclass Security:  \
    def __init__(self):\n        self.pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')\n        self.secret_key = 'mysecretkey'  # Change this\n        self.algorithm = 'HS256'\n        self.access_token_expires_minutes = 30\n\n    def verify_password(self, plain_password, hashed_password):\n        return self.pwd_context.verify(plain_password, hashed_password)\n\n    def get_password_hash(self, password):\n        return self.pwd_context.hash(password)" > app/core/security.py

# Create and populate app/models/user.py
print_message "Creating app/models/user.py..."
echo "from sqlalchemy import Column, Integer, String\nfrom database import Base\n\nclass User(Base):\n    __tablename__ = 'users'\n    id = Column(Integer, primary_key=True, index=True)\n    username = Column(String, unique=True, index=True)\n    email = Column(String, unique=True, index=True)\n    full_name = Column(String, index=True)\n    disabled = Column(Boolean, default=False)\n\nclass Empresa(Base):\n    __tablename__ = 'empresas'\n    id = Column(Integer, primary_key=True, index=True)\n    name = Column(String, index=True)\n    cnpj = Column(String, unique=True, index=True)" > app/models/user.py

# Create and populate app/schemas/user.py
print_message "Creating app/schemas/user.py..."
echo "from pydantic import BaseModel\n\nclass UserBase(BaseModel):\n    username: str\n    email: str\n    full_name: str = None\n    disabled: bool = None\n\nclass UserCreate(UserBase):\n    password: str\n\nclass UserOut(UserBase):\n    pass" > app/schemas/user.py

# Create and populate app/routers/auth.py
print_message "Creating app/routers/auth.py..."
echo "from fastapi import APIRouter, Depends\nfrom app.schemas.user import UserCreate, UserOut\nfrom app.core.security import Security\n\nrouter = APIRouter()\nsecurity = Security()\n\n@router.post('/auth/users/', response_model=UserOut)\ndef create_user(user: UserCreate):\n    # Logic to create user\n    return user" > app/routers/auth.py

# Create and populate app/dependencies.py
print_message "Creating app/dependencies.py..."
echo "from fastapi import Depends\nfrom app.core.security import Security\n\ndef get_current_user():\n    pass  # Logic to get current user" > app/dependencies.py

# Update app/main.py
print_message "Updating app/main.py..."
echo "from fastapi import FastAPI\nfrom app.routers import auth\n\napp = FastAPI(title='Guriata Contabilidade', version='1.0')\napp.include_router(auth.router)" > app/main.py

print_message "Setup completed successfully!"
echo "Next steps: Run your FastAPI application using 'uvicorn app.main:app --reload'"