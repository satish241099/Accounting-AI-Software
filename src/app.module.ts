import { Module } from '@nestjs/common'
import { ConfigModule } from '@nestjs/config'
import { AuthModule } from './auth/auth.module'
import { KernelModule } from './kernel/kernel.module'
import { RouteCoverageModule } from './route-coverage/route-coverage.module'

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env.local', '.env'],
    }),
    AuthModule,
    KernelModule,
    RouteCoverageModule,
  ],
})
export class AppModule {}