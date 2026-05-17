import { createFileRoute, useRouter } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useState } from "react";

import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { ApiError, fetchJson } from "../lib/api/client";

export const Route = createFileRoute("/login")({ component: LoginPage });

const loginSchema = z.object({
  username: z.string().min(1, "用户名必填"),
  password: z.string().min(1, "密码必填"),
});

type LoginForm = z.infer<typeof loginSchema>;

function LoginPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>();

  const onSubmit = async (values: LoginForm) => {
    setError(null);
    const parsed = loginSchema.safeParse(values);
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "表单校验失败");
      return;
    }
    try {
      await fetchJson("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(parsed.data),
      });
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      router.navigate({ to: "/repos" });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("用户名或密码错误");
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("登录失败");
      }
    }
  };

  return (
    <div className="flex justify-center pt-10">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>登录</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="username">用户名</Label>
              <Input id="username" autoComplete="username" {...register("username", { required: true })} />
              {errors.username && <span className="text-xs text-red-600">用户名必填</span>}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                {...register("password", { required: true })}
              />
              {errors.password && <span className="text-xs text-red-600">密码必填</span>}
            </div>
            {error && <div className="text-sm text-red-600">{error}</div>}
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "登录中…" : "登录"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
