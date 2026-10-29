import { NestFactory } from '@nestjs/core'
import { AppModule } from './app.module'

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule)

  app.enableCors({
    origin: process.env.CORS_ORIGIN ?? 'http://localhost:3000',
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true,
  })

  const port = process.env.PORT ?? 3001
  await app.listen(port)
  console.log(`NestJS application running on port ${port}`)
}

bootstrap().catch((err) => {
  console.error('Failed to bootstrap NestJS application', err)
  process.exit(1)
})