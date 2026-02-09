# Contributing to Aarya Clothing

Thank you for your interest in contributing to Aarya Clothing! This guide will help you understand how to contribute to this e-commerce platform.

## 🚀 Getting Started

### Prerequisites

Before you start contributing, make sure you have:

- **Python 3.11+** installed
- **Node.js 18+** installed
- **Docker & Docker Compose** installed
- **Git** configured with your name and email
- **Basic knowledge** of FastAPI, Next.js, PostgreSQL, and Redis

### Development Environment Setup

1. **Fork the Repository**
   ```bash
   # Fork the repository on GitHub
   git clone https://github.com/yourusername/Aarya_Clothing.git
   cd Aarya_Clothing
   ```

2. **Set Up Development Environment**
   ```bash
   # Copy environment file
   cp .env.example .env
   
   # Set up virtual environments
   python -m venv venv_core
   python -m venv venv_commerce
   python -m venv venv_payment
   
   # Activate environments and install dependencies
   venv_core\Scripts\activate && pip install -r services/core/requirements.txt
   venv_commerce\Scripts\activate && pip install -r services/commerce/requirements.txt
   venv_payment\Scripts\activate && pip install -r services/payment/requirements.txt
   
   # Install frontend dependencies
   cd frontend && npm install
   ```

3. **Start Development Services**
   ```bash
   # Start databases
   docker-compose up -d postgres redis
   
   # Start backend services (in separate terminals)
   cd services/core && venv_core\Scripts\activate && python main.py
   cd services/commerce && venv_commerce\Scripts\activate && python main.py
   cd services/payment && venv_payment\Scripts\activate && python main.py
   
   # Start frontend (in another terminal)
   cd frontend && npm run dev
   ```

## 🏗️ Project Structure

Understanding the project structure is essential for effective contribution:

```
Aarya_Clothing/
├── services/                    # Backend microservices
│   ├── core/                   # Authentication service
│   ├── commerce/                # Product/order service
│   └── payment/                 # Payment processing
├── frontend/                    # Next.js frontend
├── docs/                       # Documentation
├── docker/                     # Docker configurations
└── tests/                      # Test suites
```

## 🤝 How to Contribute

### 1. Reporting Issues

- **Bug Reports**: Use the issue template for bug reports
- **Feature Requests**: Use the feature request template
- **Security Issues**: Email security@aaryaclothing.com privately

### 2. Code Contributions

#### Step 1: Create an Issue
Before starting work, create an issue to discuss your proposed changes.

#### Step 2: Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

#### Step 3: Make Your Changes
Follow the coding standards and guidelines below.

#### Step 4: Test Your Changes
```bash
# Run tests
pytest tests/

# Test services manually
curl http://localhost:8001/health
curl http://localhost:8010/health
curl http://localhost:8020/health
```

#### Step 5: Submit a Pull Request
- Push to your fork
- Create a pull request with a clear description
- Link to any related issues

## 📝 Coding Standards

### Python (Backend Services)

#### Code Style
- Follow **PEP 8** guidelines
- Use **Black** for code formatting
- Use **isort** for import sorting
- Maximum line length: **88 characters**

#### Example Code Structure
```python
# services/core/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.auth import UserCreate, UserResponse
from service.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        auth_service = AuthService(db)
        user = await auth_service.create_user(user_data)
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### Documentation
- Use **docstrings** for all functions and classes
- Follow **Google style** docstrings
- Include type hints for all function parameters

```python
def create_user(
    self, 
    user_data: UserCreate, 
    db: Session
) -> User:
    """Create a new user in the database.
    
    Args:
        user_data: User creation data
        db: Database session
        
    Returns:
        Created user object
        
    Raises:
        ValueError: If user already exists
    """
    # Implementation
```

### TypeScript/JavaScript (Frontend)

#### Code Style
- Use **Prettier** for code formatting
- Use **ESLint** for linting
- Use **TypeScript** strictly
- Follow **React** best practices

#### Example Component Structure
```typescript
// frontend/src/components/product/ProductCard.tsx
import React from 'react';
import Image from 'next/image';
import { Product } from '@/types/product';
import { Button } from '@/components/ui/Button';

interface ProductCardProps {
  product: Product;
  onAddToCart: (productId: number) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onAddToCart,
}) => {
  return (
    <div className="border rounded-lg p-4">
      <Image
        src={product.images[0]}
        alt={product.name}
        width={200}
        height={200}
      />
      <h3 className="font-semibold mt-2">{product.name}</h3>
      <p className="text-gray-600">₹{product.price}</p>
      <Button onClick={() => onAddToCart(product.id)}>
        Add to Cart
      </Button>
    </div>
  );
};
```

### Database Changes

#### Migrations
- Create migration files for all schema changes
- Use descriptive migration names
- Test migrations on development data

```sql
-- migrations/001_add_product_variants.sql
ALTER TABLE products ADD COLUMN variants JSONB DEFAULT '[]';
ALTER TABLE products ADD COLUMN has_variants BOOLEAN DEFAULT false;
```

#### Documentation
- Update **MIGRATION.md** files
- Document schema changes in service READMEs

## 🧪 Testing Guidelines

### Backend Testing

#### Unit Tests
```python
# tests/test_auth_service.py
import pytest
from unittest.mock import Mock, patch
from service.auth_service import AuthService
from schemas.auth import UserCreate

def test_create_user_success():
    """Test successful user creation."""
    # Arrange
    mock_db = Mock()
    auth_service = AuthService(mock_db)
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="TestPassword123!"
    )
    
    # Act
    result = auth_service.create_user(user_data)
    
    # Assert
    assert result.email == user_data.email
    assert result.username == user_data.username
```

#### Integration Tests
```python
# tests/test_auth_endpoints.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_user():
    """Test user registration endpoint."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPassword123!"
        }
    )
    assert response.status_code == 201
    assert "id" in response.json()
```

### Frontend Testing

#### Component Tests
```typescript
// frontend/src/components/__tests__/ProductCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductCard } from '../product/ProductCard';

const mockProduct = {
  id: 1,
  name: 'Test Product',
  price: 999,
  images: ['test.jpg'],
};

describe('ProductCard', () => {
  it('renders product information correctly', () => {
    render(<ProductCard product={mockProduct} onAddToCart={jest.fn()} />);
    
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('₹999')).toBeInTheDocument();
  });

  it('calls onAddToCart when button is clicked', () => {
    const mockOnAddToCart = jest.fn();
    render(<ProductCard product={mockProduct} onAddToCart={mockOnAddToCart} />);
    
    fireEvent.click(screen.getByText('Add to Cart'));
    expect(mockOnAddToCart).toHaveBeenCalledWith(1);
  });
});
```

## 📋 Pull Request Guidelines

### Before Submitting

1. **Code Quality**
   - [ ] Code follows style guidelines
   - [ ] All tests pass
   - [ ] No linting errors
   - [ ] Documentation is updated

2. **Testing**
   - [ ] Unit tests written for new features
   - [ ] Integration tests updated
   - [ ] Manual testing completed

3. **Documentation**
   - [ ] API documentation updated
   - [ ] README files updated
   - [ ] Comments added for complex logic

### Pull Request Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## 🔧 Development Tools

### Recommended VS Code Extensions

- **Python**: Python, Pylance, Black Formatter
- **TypeScript**: TypeScript Importer, ES7+ React/Redux/React-Native snippets
- **Docker**: Docker
- **Database**: PostgreSQL
- **Git**: GitLens

### Pre-commit Hooks

Set up pre-commit hooks for code quality:

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install
```

### .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v2.7.1
    hooks:
      - id: prettier
        types_or: [javascript, jsx, ts, tsx, json, css, scss, md]
```

## 🚀 Deployment Guidelines

### Environment Variables

Never commit sensitive environment variables. Use `.env.example` for templates:

```bash
# .env.example
DATABASE_URL=postgresql://user:password@localhost:5432/db
JWT_SECRET_KEY=your-secret-key
```

### Docker Changes

- Update Dockerfiles for dependency changes
- Test Docker builds locally
- Update docker-compose.yml if needed

## 📚 Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

### Best Practices
- [12 Factor App](https://12factor.net/)
- [Microservices Patterns](https://microservices.io/patterns/)
- [API Design Guidelines](https://restfulapi.net/)

## 🤝 Community

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Maintain professional communication

### Getting Help

- **Discord**: Join our development community
- **Issues**: Create GitHub issues for bugs/features
- **Discussions**: Use GitHub Discussions for questions

## 🏆 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Annual contributor highlights

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Aarya Clothing! 🎉

## 🆘 Need Help?

If you need help with contributing:
1. Check existing issues and discussions
2. Read the documentation thoroughly
3. Join our Discord community
4. Create an issue with the "question" label

Happy coding! 🚀
