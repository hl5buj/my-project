# Django-FastAPI JWT 인증 시스템 문서

## 개요

본 프로젝트는 **Django 서버**에서 JWT(JSON Web Token)를 발급하고, **FastAPI 서버**에서 해당 토큰을 검증하는 마이크로서비스 아키텍처의 인증 시스템입니다.

### 핵심 특징

- **비대칭 암호화(RS256)**: Private Key로 서명, Public Key로 검증
- **서비스 분리**: Django(인증 서버) + FastAPI(리소스 서버)
- **토큰 기반 인증**: Stateless 인증 방식
- **확장 가능한 구조**: 여러 마이크로서비스에서 동일한 Public Key로 토큰 검증 가능

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client                                  │
│                    (웹 브라우저/모바일)                            │
└──────────────┬──────────────────────────────────┬───────────────┘
               │                                  │
               │ 1. 로그인 요청                     │ 3. API 요청 + JWT
               │ (username/password)              │
               ▼                                  ▼
┌──────────────────────────────┐    ┌───────────────────────────┐
│      Django Server           │    │    FastAPI Server         │
│   (Authentication Server)    │    │   (Resource Server)       │
├──────────────────────────────┤    ├───────────────────────────┤
│ • JWT 토큰 발급              │    │ • JWT 토큰 검증            │
│ • 사용자 인증/관리            │    │ • 보호된 리소스 제공        │
│ • Private Key로 서명         │    │ • Public Key로 검증        │
└──────────────┬───────────────┘    └───────────────────────────┘
               │                                  ▲
               │ 2. JWT 토큰 발급                  │
               │    (access + refresh)            │
               └──────────────────────────────────┘
                    Public Key 공유 (사전 배포)
```

---

## Django 서버 (JWT 발급)

### 프로젝트 구조

```
my-project/
├── config/
│   ├── settings.py          # JWT 설정
│   └── urls.py              # 토큰 엔드포인트
├── users/
│   ├── views.py             # 커스텀 토큰 발급 로직
│   └── urls.py              # 사용자 API
├── private.pem              # JWT 서명용 Private Key
└── public.pem               # JWT 검증용 Public Key
```

### JWT 설정 (config/settings.py:144-157)

```python
# RSA 키 로드
with open(os.path.join(BASE_DIR, 'private.pem')) as f:
    PRIVATE_KEY = f.read()

with open(os.path.join(BASE_DIR, 'public.pem')) as f:
    PUBLIC_KEY = f.read()

# JWT 설정
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=120),    # 액세스 토큰 2시간
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),        # 리프레시 토큰 1일
    'ALGORITHM': 'RS256',                               # RSA 비대칭 암호화
    'SIGNING_KEY': PRIVATE_KEY,                         # 서명용 Private Key
    'VERIFYING_KEY': PUBLIC_KEY,                        # 검증용 Public Key
    'AUTH_HEADER_TYPES': ('Bearer',),                   # Authorization 헤더 타입
}
```

### 커스텀 토큰 발급 (users/views.py:24-42)

```python
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT 토큰에 추가 사용자 정보를 포함하는 Serializer"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # 토큰 페이로드에 사용자 정보 추가
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = "instructor"
        token['premium'] = True
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # 응답에 사용자 정보 추가
        user_serializer = UserSerializer(self.user)
        data['user'] = user_serializer.data
        return data
```

### API 엔드포인트

| 엔드포인트 | 메서드 | 설명 | 인증 필요 |
|----------|--------|------|----------|
| `/api/token/` | POST | JWT 토큰 발급 (로그인) | ❌ |
| `/api/token/refresh/` | POST | 액세스 토큰 갱신 | ❌ |
| `/api/users/me/` | GET | 현재 사용자 정보 조회 | ✅ |

### 토큰 발급 예시

**요청:**
```http
POST /api/token/
Content-Type: application/json

{
    "username": "testuser",
    "password": "testpass123"
}
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

**토큰 페이로드 (decoded):**
```json
{
    "token_type": "access",
    "exp": 1730284800,
    "iat": 1730277600,
    "jti": "abc123...",
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "instructor",
    "premium": true
}
```

---

## FastAPI 서버 (JWT 검증)

### 프로젝트 구조

```
myapp-fastapi/
├── main.py                  # FastAPI 애플리케이션
├── auth.py                  # JWT 검증 로직
├── public.pem               # Django에서 복사한 Public Key
└── requirements.txt
```

### JWT 검증 로직 (auth.py)

```python
# Public Key 로드
with open('public.pem', encoding='utf-8') as f:
    PUBLIC_KEY = f.read()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """JWT 토큰을 검증하고 사용자 정보를 반환"""
    token = credentials.credentials

    try:
        # Public Key로 토큰 검증
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"]
        )

        # 사용자 정보 추출
        return {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="토큰이 만료되었습니다"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 토큰입니다"
        )
```

### API 엔드포인트

| 엔드포인트 | 메서드 | 설명 | 인증 필요 |
|----------|--------|------|----------|
| `/` | GET | 헬스 체크 | ❌ |
| `/protected` | GET | 보호된 리소스 (테스트용) | ✅ |
| `/upload` | POST | 파일 업로드 API | ✅ |

### 보호된 엔드포인트 사용 예시

**요청:**
```http
GET /protected
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**응답:**
```json
{
    "message": "인증 성공!",
    "user_id": 1,
    "username": "testuser"
}
```

---

## 인증 흐름

### 1. 초기 로그인

```
Client                 Django Server              FastAPI Server
  │                         │                          │
  │──── POST /api/token/ ──>│                          │
  │   {username, password}  │                          │
  │                         │                          │
  │<── JWT Tokens + User ───│                          │
  │   {access, refresh}     │                          │
  │                         │                          │
```

### 2. API 요청

```
Client                 Django Server              FastAPI Server
  │                         │                          │
  │────── GET /protected ──────────────────────────────>│
  │    Authorization: Bearer <access_token>            │
  │                         │                          │
  │                         │                          │<── Public Key 검증
  │                         │                          │
  │<──────────── 리소스 반환 ───────────────────────────│
  │    {message, user_id, username}                    │
  │                         │                          │
```

### 3. 토큰 갱신

```
Client                 Django Server              FastAPI Server
  │                         │                          │
  │── POST /api/token/refresh/ ─>│                     │
  │   {refresh: <token>}    │                          │
  │                         │                          │
  │<── New Access Token ────│                          │
  │   {access}              │                          │
  │                         │                          │
```

---

## 보안 고려사항

### 1. 키 관리

**✅ 권장사항:**
- Private Key는 **절대 외부 공개 금지**
- Public Key는 필요한 서비스에만 배포
- 프로덕션 환경에서는 환경 변수나 비밀 관리 시스템 사용
- 키는 Git에 포함하지 않음 (`.gitignore` 추가)

**🔒 키 보안:**
```bash
# Private Key 권한 설정 (Unix 계열)
chmod 600 private.pem

# Public Key 권한 설정
chmod 644 public.pem
```

### 2. 토큰 수명

- **Access Token**: 2시간 (짧게 유지하여 탈취 위험 최소화)
- **Refresh Token**: 1일 (Access Token 갱신용)

### 3. HTTPS 사용

프로덕션 환경에서는 **반드시 HTTPS** 사용:
- 토큰 전송 시 암호화
- Man-in-the-middle 공격 방지

### 4. CORS 설정

**Django (config/settings.py:133):**
```python
# 개발 환경
CORS_ALLOW_ALL_ORIGINS = True  # 개발용

# 프로덕션 환경
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend.com",
    "https://your-fastapi.com"
]
```

---

## RS256 vs HS256 비교

| 특징 | RS256 (본 프로젝트) | HS256 (대칭키) |
|------|-------------------|---------------|
| **암호화 방식** | 비대칭 (Public/Private Key) | 대칭 (Shared Secret) |
| **서명** | Private Key | Shared Secret |
| **검증** | Public Key | Shared Secret |
| **키 공유** | Public Key만 공유 (안전) | Secret 공유 필요 (위험) |
| **마이크로서비스** | ✅ 이상적 | ⚠️ 보안 취약 |
| **성능** | 느림 | 빠름 |
| **사용 사례** | 서비스 간 인증 | 단일 서버 |

**RS256 장점:**
- Public Key만 배포하므로 보안성 높음
- 여러 서비스에서 독립적으로 토큰 검증 가능
- Private Key 유출 없이 확장 가능

---

## 설정 및 실행 방법

### Django 서버 설정

```bash
# 1. 가상환경 생성 및 활성화
cd my-project
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers

# 3. 데이터베이스 마이그레이션
python manage.py migrate

# 4. 슈퍼유저 생성
python manage.py createsuperuser

# 5. 서버 실행
python manage.py runserver
```

### FastAPI 서버 설정

```bash
# 1. 가상환경 생성 및 활성화
cd myapp-fastapi
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. Public Key 복사
# Django의 public.pem을 FastAPI 루트 디렉토리에 복사

# 4. 서버 실행
uvicorn main:app --reload --port 8001
```

### 테스트 시나리오

```bash
# 1. Django에서 토큰 발급
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# 2. 발급받은 토큰으로 FastAPI 보호된 엔드포인트 접근
curl http://localhost:8001/protected \
  -H "Authorization: Bearer <access_token>"
```

---

## 확장 가능성

### 1. 추가 마이크로서비스

동일한 Public Key를 사용하여 무한 확장 가능:

```
Django (Auth)
    │
    │ Public Key 배포
    │
    ├──> FastAPI (리소스 서버 1)
    │
    ├──> Node.js (리소스 서버 2)
    │
    └──> Go (리소스 서버 3)
```

### 2. 권한 관리 (Role-Based Access Control)

토큰 페이로드의 `role` 필드 활용:

```python
# FastAPI에서 권한 확인
def check_role(required_role: str):
    def role_checker(current_user: Dict = Depends(get_current_user)):
        if current_user.get("role") != required_role:
            raise HTTPException(status_code=403, detail="권한이 없습니다")
        return current_user
    return role_checker

# 사용 예시
@app.get("/admin/dashboard")
def admin_dashboard(user: Dict = Depends(check_role("admin"))):
    return {"message": "관리자 대시보드"}
```

### 3. 토큰 블랙리스트

로그아웃 시 토큰 무효화:
- Redis를 사용하여 블랙리스트 관리
- 토큰의 `jti` (JWT ID) 저장

---

## 문제 해결

### 토큰 검증 실패

**증상:** `유효하지 않은 토큰입니다` 에러

**원인 및 해결:**
1. **Public Key 불일치**
   - Django와 FastAPI의 `public.pem` 파일이 동일한지 확인

2. **알고리즘 불일치**
   - Django: `ALGORITHM': 'RS256'`
   - FastAPI: `algorithms=["RS256"]`
   - 양쪽 모두 동일한지 확인

3. **토큰 만료**
   - 토큰 발급 시간 확인
   - Access Token 수명: 2시간

### CORS 에러

**증상:** 브라우저에서 API 호출 시 CORS 에러

**해결:**
```python
# Django settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # 프론트엔드 주소
    "http://localhost:8001",  # FastAPI 주소
]
```

---

## 기술 스택

### Django 서버
- **Django 5.1.2**
- **Django REST Framework**
- **djangorestframework-simplejwt**: JWT 토큰 발급/검증
- **django-cors-headers**: CORS 설정
- **PyJWT**: JWT 라이브러리
- **cryptography**: RSA 암호화

### FastAPI 서버
- **FastAPI**: 비동기 웹 프레임워크
- **PyJWT**: JWT 검증
- **Uvicorn**: ASGI 서버

---

## 참고 자료

- [JWT.io](https://jwt.io/): JWT 디버깅 도구
- [Django REST Framework SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [RFC 7519 - JWT Specification](https://tools.ietf.org/html/rfc7519)
- [RS256 vs HS256](https://auth0.com/blog/rs256-vs-hs256-whats-the-difference/)

---

## 라이센스 및 연락처

- **프로젝트 목적**: 학습 및 개발용
- **작성일**: 2025-10-30
- **버전**: 1.0

---

**문서 작성**: Claude Code
**최종 업데이트**: 2025-10-30
