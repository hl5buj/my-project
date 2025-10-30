# Django JWT Authentication Server

Django 기반 JWT 토큰 발급 서버 (RS256 비대칭 암호화)

## 프로젝트 개요

본 프로젝트는 **Django**에서 RS256 알고리즘을 사용하여 JWT 토큰을 발급하고, **FastAPI** 등의 다른 마이크로서비스에서 Public Key를 통해 토큰을 검증할 수 있는 인증 시스템입니다.

### 주요 특징

- **RS256 비대칭 암호화**: Private Key로 서명, Public Key로 검증
- **마이크로서비스 아키텍처**: 여러 서비스에서 동일한 Public Key로 토큰 검증
- **확장 가능한 토큰 페이로드**: 사용자 정보를 토큰에 포함
- **RESTful API**: Django REST Framework 기반

## 시스템 구성

```
Django Server (my-project)          FastAPI Server (myapp-fastapi)
─────────────────────────          ────────────────────────────────
• JWT 토큰 발급 (RS256)    ─────>   • JWT 토큰 검증 (Public Key)
• Private Key로 서명                • 보호된 리소스 제공
• 사용자 인증/관리                  • user_id, username 추출
```

## 기술 스택

- Django 5.1.2
- Django REST Framework
- djangorestframework-simplejwt
- django-cors-headers
- SQLite (개발용)

## 토큰 정보

### 토큰 수명
- **Access Token**: 120분 (2시간)
- **Refresh Token**: 1일

### 토큰 페이로드
```json
{
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "instructor",
    "premium": true,
    "exp": 1730284800,
    "iat": 1730277600
}
```

## API 엔드포인트

| 엔드포인트 | 메서드 | 설명 | 인증 |
|----------|--------|------|------|
| `/api/token/` | POST | JWT 토큰 발급 | ❌ |
| `/api/token/refresh/` | POST | Access Token 갱신 | ❌ |
| `/api/users/me/` | GET | 현재 사용자 정보 | ✅ |

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers
```

### 2. 데이터베이스 마이그레이션

```bash
python manage.py migrate
```

### 3. 슈퍼유저 생성

```bash
python manage.py createsuperuser
```

### 4. 서버 실행

```bash
python manage.py runserver
```

서버는 `http://localhost:8000`에서 실행됩니다.

## 사용 예시

### 토큰 발급

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

**응답:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
}
```

### 사용자 정보 조회

```bash
curl http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer <access_token>"
```

## 연동 프로젝트

### FastAPI Server (myapp-fastapi)

Django에서 발급한 JWT 토큰을 검증하는 FastAPI 서버

**위치**: `D:\MyPython\myapp-fastapi`

**주요 기능**:
- Public Key를 사용한 JWT 토큰 검증
- 보호된 API 엔드포인트 제공
- 토큰에서 사용자 정보 추출

**엔드포인트**:
- `GET /`: 헬스 체크
- `GET /protected`: 보호된 리소스 (인증 필요)
- `POST /upload`: 파일 업로드 (인증 필요)

## 보안 고려사항

### RSA 키 관리

- `private.pem`: **절대 외부 공개 금지** (Django 서버에만 보관)
- `public.pem`: 필요한 서비스에 배포 가능
- Git 저장소에 포함하지 않음 (`.gitignore` 추가 권장)

### 프로덕션 환경

1. **HTTPS 사용 필수**
2. **환경 변수로 키 관리**
3. **CORS 설정 제한**
   ```python
   CORS_ALLOWED_ORIGINS = [
       "https://your-frontend.com",
       "https://your-api.com"
   ]
   ```

## 프로젝트 구조

```
my-project/
├── config/
│   ├── settings.py          # JWT 설정 (RS256, 토큰 수명)
│   └── urls.py              # 토큰 발급 엔드포인트
├── users/
│   ├── views.py             # 커스텀 토큰 발급 로직
│   └── urls.py              # 사용자 API
├── claudedocs/
│   └── JWT_Authentication_System.md  # 상세 문서
├── private.pem              # Private Key (서명용)
├── public.pem               # Public Key (검증용)
└── manage.py
```

## 상세 문서

프로젝트의 전체 아키텍처, 인증 흐름, 보안 가이드라인은 다음 문서를 참조하세요:

📄 **[JWT Authentication System 상세 문서](./claudedocs/JWT_Authentication_System.md)**

## 라이센스

학습 및 개발용 프로젝트

---

**최종 업데이트**: 2025-10-30
