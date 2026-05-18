import { createFileRoute, useRouter } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useState } from "react";

import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { ApiError } from "../lib/api/client";
import { useCreateRepo } from "../lib/api/queries";

export const Route = createFileRoute("/repos/new")({ component: NewRepoPage });

const LAYERS = ["bronze", "silver", "gold"] as const;
const SUBTYPES_BY_LAYER: Record<string, string[]> = {
  bronze: ["pdf", "pdf-collection", "book", "webpage", "webpage-collection", "image-set", "raw"],
  silver: ["text-corpus", "dialog-corpus", "image-text-pairs", "qa-records"],
  gold: ["cpt", "sft", "dpo", "rlhf-pref", "eval"],
};
const VISIBILITIES = ["private", "internal", "public"] as const;

const schema = z.object({
  owner: z.string().min(1, "owner 必填"),
  name: z.string().min(1, "name 必填"),
  layer: z.enum(LAYERS),
  subtype: z.string().min(1, "subtype 必填"),
  visibility: z.enum(VISIBILITIES),
  description: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

function NewRepoPage() {
  const router = useRouter();
  const createRepo = useCreateRepo();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    defaultValues: {
      owner: "",
      name: "",
      layer: "bronze",
      subtype: "pdf",
      visibility: "private",
      description: "",
    },
  });

  const selectedLayer = watch("layer");
  const subtypeOptions = SUBTYPES_BY_LAYER[selectedLayer] ?? [];

  const onSubmit = async (values: FormData) => {
    setError(null);
    const parsed = schema.safeParse(values);
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "表单校验失败");
      return;
    }
    try {
      await createRepo.mutateAsync({
        owner: parsed.data.owner,
        name: parsed.data.name,
        layer: parsed.data.layer,
        subtype: parsed.data.subtype,
        visibility: parsed.data.visibility,
        description: parsed.data.description || null,
      });
      router.navigate({
        to: "/repos/$owner/$name",
        params: { owner: parsed.data.owner, name: parsed.data.name },
        search: { tab: "files" },
      });
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("已存在同名 repository");
      } else if (err instanceof ApiError && err.status === 403) {
        setError("仅 admin 可建 repository");
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("创建失败");
      }
    }
  };

  return (
    <div className="flex justify-center pt-6">
      <Card className="w-full max-w-xl">
        <CardHeader>
          <CardTitle>新建 Repository</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="flex flex-col gap-4"
            noValidate
          >
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="owner">owner</Label>
                <Input id="owner" {...register("owner", { required: true })} />
                {errors.owner && (
                  <span className="text-xs text-red-600">owner 必填</span>
                )}
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="name">name</Label>
                <Input id="name" {...register("name", { required: true })} />
                {errors.name && (
                  <span className="text-xs text-red-600">name 必填</span>
                )}
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="layer">layer</Label>
                <select
                  id="layer"
                  className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm"
                  {...register("layer")}
                >
                  {LAYERS.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="subtype">subtype</Label>
                <select
                  id="subtype"
                  className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm"
                  {...register("subtype")}
                >
                  {subtypeOptions.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="visibility">visibility</Label>
                <select
                  id="visibility"
                  className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm"
                  {...register("visibility")}
                >
                  {VISIBILITIES.map((v) => (
                    <option key={v} value={v}>
                      {v}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="description">description (可选)</Label>
              <Textarea
                id="description"
                rows={3}
                {...register("description")}
              />
            </div>
            {error && <div className="text-sm text-red-600">{error}</div>}
            <div className="flex gap-2 justify-end">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.navigate({ to: "/repos" })}
              >
                取消
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "创建中…" : "创建"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
