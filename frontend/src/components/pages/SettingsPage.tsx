import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAppStore } from "@/stores/appStore";
import { useHealthCheck } from "@/hooks/useApi";
import Card from "@/components/ui/Card";

const settingsSchema = z.object({
  openai_api_key: z.string().optional(),
  target_language: z.string().min(2, "Ingresa un código de idioma válido (ej: es, en)"),
  batch_size: z
    .number({ message: "Debe ser un número válido" })
    .min(100, "El tamaño mínimo de lote es 100")
    .max(5000, "El tamaño máximo de lote es 5000"),
});

type SettingsSchema = z.infer<typeof settingsSchema>;

export default function SettingsPage() {
  const currentSettings = useAppStore((state) => state.settings);
  const updateSettings = useAppStore((state) => state.updateSettings);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const { refetch: testHealth, isFetching: testingHealth, data: healthData } = useHealthCheck();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SettingsSchema>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      target_language: currentSettings.target_language || "es",
      batch_size: 1000,
    },
  });

  const onSubmit = (data: SettingsSchema) => {
    updateSettings({
      target_language: data.target_language,
      export_formats: ["json"],
      batch_size: data.batch_size,
      openai_api_key: data.openai_api_key,
    });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Encabezado */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">
          Configuración Global del Sistema
        </h1>
        <p className="text-slate-600 text-sm mt-1">
          Ajusta los parámetros predeterminados de traducción, límites de batch y claves de proveedores de IA.
        </p>
      </div>

      {/* Formulario */}
      <Card title="Ajustes de Proveedor e Idioma">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* OpenAI API Key */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Clave de API de OpenAI (OPENAI_API_KEY)
            </label>
            <p className="text-xs text-slate-500 mb-2">
              Se utiliza para enviar las llamadas de generación y evaluación de prompts a los modelos GPT.
            </p>
            <input
              type="password"
              placeholder="sk-..."
              {...register("openai_api_key")}
              className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Idioma Objetivo */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Idioma Predeterminado
              </label>
              <input
                type="text"
                placeholder="es"
                {...register("target_language")}
                className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
              {errors.target_language && (
                <p className="text-xs text-rose-600 mt-1">{errors.target_language.message}</p>
              )}
            </div>

            {/* Tamaño de Batch */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Límite de Registros por Batch
              </label>
              <input
                type="number"
                placeholder="1000"
                {...register("batch_size", { valueAsNumber: true })}
                className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
              {errors.batch_size && (
                <p className="text-xs text-rose-600 mt-1">{errors.batch_size.message}</p>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-4 pt-2">
            <button
              type="submit"
              className="py-3 px-6 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded-xl shadow-sm transition-colors"
            >
              Guardar Configuración
            </button>

            {savedSuccess && (
              <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
                ✓ Ajustes guardados correctamente
              </span>
            )}
          </div>
        </form>
      </Card>

      {/* Estado del Servidor */}
      <Card title="Estado de la Infraestructura">
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <p className="text-xs font-bold text-slate-500 uppercase">Backend API</p>
              <p className="text-base font-bold text-slate-900 mt-0.5">FastAPI 0.115</p>
            </div>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <p className="text-xs font-bold text-slate-500 uppercase">Base de Datos</p>
              <p className="text-base font-bold text-slate-900 mt-0.5">PostgreSQL 16</p>
            </div>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <p className="text-xs font-bold text-slate-500 uppercase">Tokenizador</p>
              <p className="text-base font-bold text-slate-900 mt-0.5">tiktoken (o200k_base)</p>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-between border-t border-slate-100">
            <div>
              <p className="text-xs font-semibold text-slate-700">Verificar estado de la conexión</p>
              <p className="text-xs text-slate-500">Comprueba la salud del servicio REST backend.</p>
            </div>
            <button
              type="button"
              onClick={() => testHealth()}
              disabled={testingHealth}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-xl transition-colors border border-slate-300"
            >
              {testingHealth ? "Verificando..." : "Probar Conexión"}
            </button>
          </div>

          {healthData && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-mono">
              Status response: {JSON.stringify(healthData)}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}