# ws://localhost:8080/ws

几乎所有的ws请求都需要先在`http`请求中获取`ticket`或`uuid`

例如`ws://localhost:8080/ws/v1/ai-chat?uuid=****`

变量名使用`uuid`是指其有其他用途

## /test

回复：

```typescript
`Kotlin springboot4 received: ${userText}`
```

## /v1/ai-chat

param: uuid: String

回复：

```typescript
undefined
```