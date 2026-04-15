# http://localhost:8080/api

所有返回的json对象总有如下格式

```typescript
class respose<T> {
    "code": number;
    "message": string;
    "data": T
}
```

接下来将省略`/api`并只给出`T`的类声明

当`"code"`不是`200`时，`"data"`必定为`null`

部分`/api/test`的返回值不遵循上述格式

## /test

### GET /hello

Authorization: Bearer $Token

key: 无

回复：

```typescript
"Hello Kotlin WebFlux!"
```

## /v1/auth

### POST /login

Authorization: 无

key: username, password

data：

```typescript
class data {
    "username": string;
    "role": string;
    "token": string;
    "expire": Date;
}
```

### GET /logout

Authorization: Bearer $Token

key: 无

data：

```typescript
null
```

### GET /ask-code?email=******&type=register

Authorization: 无

key: 无

data：

```typescript
null
```

### GET /ask-code?email=******&type=reset

Authorization: 无

key: 无

data：

```typescript
null
```

### POST /register

Authorization: 无

key: 无

data：email, code, username, password

```typescript
null
```

### POST /reset

Authorization: 无

key: email, code, password

data：

```typescript
null
```

### GET /relogin

Authorization: Bearer $Token

key: 无

data：

```typescript
class data {
    "token": sting;
    "expire": time
}
```

## /v1/upload

### POST /file

Authorization: Bearer $Token

key: file, type: String

data：

```typescript
null
```

## /v1/download

### GET /file

Authorization: Bearer $Token

key: type: String

data：

```typescript
undefined
```

## /v1/ai-chat

### GET /new-chat

Authorization: Bearer $Token

key: 无

data：

```typescript
undefined
```
