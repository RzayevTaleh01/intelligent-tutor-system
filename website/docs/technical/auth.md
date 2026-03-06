---
sidebar_position: 1
title: Auth & Multi-Tenancy
---

# Authentication & Multi-Tenancy

## Overview

EduVision ITS implements a robust **Multi-Tenant Architecture** designed to support multiple organizations (Schools, Universities) within a single deployment. Security is enforced via **Role-Based Access Control (RBAC)** and **JWT (JSON Web Token)** authentication.

## 🏢 Multi-Tenancy Model

The system uses a **Data Isolation** strategy where all data is stored in a shared database schema, but every critical table (`User`, `Course`, `Session`) includes a `tenant_id` foreign key.

### Tenant Entity
Defined in `src/db/models_prod.py`:
*   **ID:** Unique UUID.
*   **Name:** Organization name (e.g., "Baku State University").
*   **Domain:** White-label domain configuration.

### Data Isolation Logic
All database queries are automatically scoped to the current user's `tenant_id`. This prevents data leakage between organizations.

```python
# Example of tenant-scoped query
stmt = select(User).where(
    User.email == email,
    User.tenant_id == current_user.tenant_id  # Automatic filter
)
```

## 🔐 Authentication Flow

The system follows the **OAuth2 Password Bearer** flow.

1.  **Registration (`POST /auth/register`)**:
    *   User provides `email`, `password`, and `tenant_id`.
    *   Password is hashed using `bcrypt`.
    *   User is created with default role `student`.

2.  **Login (`POST /auth/login`)**:
    *   User submits credentials.
    *   System verifies hash.
    *   Returns `access_token` (JWT) containing `sub` (user_id) and `role`.

3.  **Protected Routes**:
    *   Middleware verifies the JWT signature.
    *   Injects `current_user` into the request context.

## 🛡️ Role-Based Access Control (RBAC)

We implement three distinct roles in `src/auth/utils.py`:

| Role | Permissions |
| :--- | :--- |
| **Admin** | Full system access. Can create tenants, manage all users, and view global analytics. |
| **Teacher** | Can create courses, upload materials, and view student progress within their tenant. |
| **Student** | Can enroll in courses, start sessions, and interact with the Tutor. |

### Decorator Usage

```python
@router.post("/courses/")
def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_active_teacher) # Enforces Teacher role
):
    ...
```

## 🔑 Security Best Practices
*   **Password Hashing:** Uses `passlib` with `bcrypt` scheme.
*   **Token Expiry:** Access tokens expire after 30 minutes (configurable).
*   **CORS:** Configured to allow specific frontend origins only.
