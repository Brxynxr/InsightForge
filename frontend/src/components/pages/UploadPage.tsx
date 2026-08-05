import React, { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link } from "react-router-dom";
import { useAnalyzeReviews } from "@/hooks/useApi";
import Card from "@/components/ui/Card";

const schema = z.object({
  file: z
    .custom<FileList>()
    .refine(
      (files) => files && files.length > 0,
      "Se requiere seleccionar un archivo Excel o CSV"
    ),
  review_column: z.string().min(1, "El nombre de la columna es requerido"),
  optimize_tokens: z.boolean(),
  target_language: z.string().min(2, "Código de idioma requerido"),
});

type Schema = z.infer<typeof schema>;

function useTimer() {
  const [elapsed, setElapsed] = useState(0);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const start = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setElapsed(0);
    setRunning(true);
    intervalRef.current = setInterval(() => {
      setElapsed((prev) => prev + 10);
    }, 10);
  };

  const stop = () => {
    setRunning(false);
    if (intervalRef.current) clearInterval(intervalRef.current);
  };

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return { elapsed, running, start, stop };
}

function formatTime(ms: number) {
  const totalSeconds = ms / 1000;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  const centiseconds = Math.floor((ms % 1000) / 10);
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}.${String(centiseconds).padStart(2, "0")}`;
}

export default function UploadPage() {
  const mutation = useAnalyzeReviews();
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const timer = useTimer();

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<Schema>({
    resolver: zodResolver(schema),
    defaultValues: {
      review_column: "reseña",
      optimize_tokens: true,
      target_language: "en",
    },
  });

  const optimizeTokens = watch("optimize_tokens");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFileName(e.target.files[0].name);
    } else {
      setSelectedFileName(null);
    }
  };

  const onSubmit = (data: Schema) => {
    if (!data.file || data.file.length === 0) return;

    const formData = new FormData();
    formData.append("file", data.file[0]);
    formData.append("review_column", data.review_column);
    formData.append("optimize_tokens", String(data.optimize_tokens));
    formData.append("target_language", data.target_language);

    timer.start();
    mutation.mutate(formData, {
      onSettled: () => timer.stop(),
    });
  };

  const analysisData = mutation.data;
  const tokenComp = analysisData?.token_comparison;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">
          Análisis de Reseñas de App Store
        </h1>
        <p className="text-slate-600 text-sm mt-1">
          Sube un archivo Excel con reseñas para clasificar errores técnicos,
          extraer componentes afectados y comparar costos de tokens.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-7">
          <Card title="1. Configurar Análisis">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Archivo Excel con Reseñas
                </label>
                <div className="relative border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-6 text-center bg-slate-50 transition-colors">
                  <input
                    type="file"
                    accept=".xlsx,.xls,.csv"
                    {...register("file", { onChange: handleFileChange })}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <div className="flex flex-col items-center justify-center space-y-2 pointer-events-none">
                    <div className="p-3 bg-blue-100 text-blue-600 rounded-full">
                      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 0115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    {selectedFileName ? (
                      <p className="text-sm font-bold text-blue-600 bg-blue-50 px-3 py-1 rounded-md border border-blue-200">
                        📄 {selectedFileName}
                      </p>
                    ) : (
                      <>
                        <p className="text-sm font-semibold text-slate-700">
                          Haz clic o arrastra tu archivo aquí
                        </p>
                        <p className="text-xs text-slate-500">
                          .xlsx, .xls, .csv — Columna de reseñas requerida
                        </p>
                      </>
                    )}
                  </div>
                </div>
                {errors.file && (
                  <p className="text-xs font-medium text-rose-600 mt-1.5">
                    {errors.file.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">
                  Nombre de la Columna con la Reseña
                </label>
                <p className="text-xs text-slate-500 mb-2">
                  Debe coincidir exactamente con el encabezado de la columna en tu
                  Excel. Ejemplo: <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">reseña</code>
                </p>
                <input
                  type="text"
                  placeholder="reseña"
                  {...register("review_column")}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
                {errors.review_column && (
                  <p className="text-xs text-rose-600 mt-1">{errors.review_column.message}</p>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1">
                    Idioma de Destino
                  </label>
                  <select
                    {...register("target_language")}
                    className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  >
                    <option value="en">Inglés (en)</option>
                    <option value="es">Español (es)</option>
                    <option value="pt">Portugués (pt)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1">
                    Optimización de Tokens
                  </label>
                  <div className="flex items-center space-x-3 h-[42px] px-3.5 border border-slate-300 rounded-xl bg-white">
                    <input
                      type="checkbox"
                      {...register("optimize_tokens")}
                      className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-slate-700">
                      {optimizeTokens ? "Traducir antes de analizar" : "Analizar directo"}
                    </span>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={mutation.isPending || !selectedFileName}
                className="w-full py-3.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold rounded-xl shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2"
              >
                {mutation.isPending ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                    </svg>
                    <span>Analizando reseñas...</span>
                  </>
                ) : (
                  <span>Ejecutar Análisis</span>
                )}
              </button>

              {mutation.isError && (
                <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
                  <strong>Error:</strong> {(mutation.error as Error).message}
                </div>
              )}
            </form>
          </Card>
        </div>

        <div className="lg:col-span-5 space-y-6">
          {/* Cronómetro animado */}
          {(mutation.isPending || analysisData) && (
            <div className={`relative overflow-hidden rounded-2xl border-2 p-6 text-center transition-all duration-500 ${
              mutation.isPending
                ? "border-blue-400 bg-gradient-to-br from-blue-50 to-indigo-50 shadow-lg shadow-blue-100"
                : "border-emerald-400 bg-gradient-to-br from-emerald-50 to-teal-50 shadow-lg shadow-emerald-100"
            }`}>
              {/* Anillo animado */}
              <div className="relative inline-block mb-3">
                <svg className={`w-24 h-24 ${mutation.isPending ? "animate-spin" : ""}`} viewBox="0 0 100 100">
                  <circle
                    cx="50" cy="50" r="42"
                    fill="none"
                    stroke={mutation.isPending ? "#bfdbfe" : "#a7f3d0"}
                    strokeWidth="6"
                  />
                  <circle
                    cx="50" cy="50" r="42"
                    fill="none"
                    stroke={mutation.isPending ? "#2563eb" : "#059669"}
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray="264"
                    strokeDashoffset={mutation.isPending ? "66" : "0"}
                    className="transition-all duration-1000"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <svg className={`w-8 h-8 ${mutation.isPending ? "text-blue-600" : "text-emerald-600"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>

              {/* Tiempo */}
              <p className={`text-4xl font-black font-mono tracking-wider ${
                mutation.isPending ? "text-blue-700" : "text-emerald-700"
              }`}>
                {formatTime(timer.elapsed)}
              </p>

              <p className={`text-sm font-semibold mt-2 ${
                mutation.isPending ? "text-blue-600" : "text-emerald-600"
              }`}>
                {mutation.isPending ? "Procesando..." : "✅ Análisis completado"}
              </p>

              {analysisData && !mutation.isPending && (
                <div className="mt-3 flex items-center justify-center space-x-4 text-xs">
                  <span className="bg-white/80 px-2.5 py-1 rounded-lg border border-emerald-200 font-bold text-emerald-700">
                    {analysisData.metrics.total_records_input as number || 0} registros
                  </span>
                  <span className="bg-white/80 px-2.5 py-1 rounded-lg border border-emerald-200 font-bold text-emerald-700">
                    {analysisData.metrics.reviews_per_second as number || 0} reg/seg
                  </span>
                </div>
              )}
            </div>
          )}

          {analysisData ? (
            <>
              <Card title="Métricas del Proceso">
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-blue-50 p-3 rounded-xl text-center">
                      <p className="text-xs font-bold text-blue-600 uppercase">Registros</p>
                      <p className="text-2xl font-black text-blue-900">
                        {(analysisData.metrics.total_records_input as number || 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="bg-indigo-50 p-3 rounded-xl text-center">
                      <p className="text-xs font-bold text-indigo-600 uppercase">Tokens Input</p>
                      <p className="text-2xl font-black text-indigo-900">
                        {(analysisData.metrics.total_input_tokens as number || 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-xl text-center">
                      <p className="text-xs font-bold text-purple-600 uppercase">Tokens/Reg</p>
                      <p className="text-2xl font-black text-purple-900">
                        {analysisData.metrics.reviews_per_second as number || 0}
                      </p>
                    </div>
                    <div className="bg-emerald-50 p-3 rounded-xl text-center">
                      <p className="text-xs font-bold text-emerald-600 uppercase">Reseñas Vacías</p>
                      <p className="text-2xl font-black text-emerald-900">
                        {analysisData.metrics.empty_reviews as number || 0}
                      </p>
                    </div>
                  </div>

                  {analysisData.results && analysisData.results.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold uppercase text-slate-500 mb-2">
                        Muestra de Análisis (primeros 3)
                      </h4>
                      <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                        {analysisData.results.slice(0, 3).map((r: Record<string, unknown>, i: number) => (
                          <div
                            key={i}
                            className="bg-slate-900 text-slate-200 text-xs p-3 rounded-xl font-mono overflow-x-auto"
                          >
                            <span className="text-blue-400 font-bold block mb-1">
                              Registro #{i + 1}
                            </span>
                            <pre className="whitespace-pre-wrap">{JSON.stringify(r, null, 2)}</pre>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <Link
                    to="/history"
                    className="block w-full text-center py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm rounded-xl transition-colors"
                  >
                    Ver en Historial Completo
                  </Link>
                </div>
              </Card>

              {tokenComp && (
                <Card title="Comparación de Costos">
                  <div className="space-y-4 text-sm">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-slate-50 p-3 rounded-xl border">
                        <p className="text-xs font-bold text-slate-500 uppercase">Original</p>
                        <p className="text-lg font-black text-slate-900">
                          {tokenComp.total_original_tokens.toLocaleString()}
                        </p>
                        <p className="text-xs text-slate-500">tokens</p>
                      </div>
                      <div className="bg-blue-50 p-3 rounded-xl border border-blue-200">
                        <p className="text-xs font-bold text-blue-600 uppercase">Traducido</p>
                        <p className="text-lg font-black text-blue-900">
                          {tokenComp.total_translated_tokens.toLocaleString()}
                        </p>
                        <p className="text-xs text-blue-600">
                          {tokenComp.percentage_reduction}% menos
                        </p>
                      </div>
                    </div>

                    <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-200">
                      <p className="text-xs font-bold text-emerald-700 uppercase mb-2">
                        Ahorro Económico
                      </p>
                      <div className="flex items-center justify-between">
                        <span className="text-emerald-700">Sin optimizar:</span>
                        <span className="font-bold text-emerald-900">
                          ${tokenComp.cost_original_usd.toFixed(4)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-emerald-700">Con optimización:</span>
                        <span className="font-bold text-emerald-900">
                          ${tokenComp.cost_translated_usd.toFixed(4)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-emerald-300">
                        <span className="text-emerald-700 font-bold">Ahorro total:</span>
                        <span className="font-black text-emerald-900 text-lg">
                          ${tokenComp.cost_savings_usd.toFixed(4)}
                        </span>
                      </div>
                    </div>

                    {tokenComp.daily_projection_10k && (
                      <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-200">
                        <p className="text-xs font-bold text-indigo-700 uppercase mb-2">
                          Proyección a 10,000 reseñas/día
                        </p>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-indigo-700">Costo sin optimizar:</span>
                          <span className="font-bold text-indigo-900">
                            ${tokenComp.daily_projection_10k.cost_original_usd.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm mt-1">
                          <span className="text-indigo-700">Costo optimizado:</span>
                          <span className="font-bold text-indigo-900">
                            ${tokenComp.daily_projection_10k.cost_translated_usd.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm mt-2 pt-2 border-t border-indigo-300">
                          <span className="text-indigo-700 font-bold">Ahorro diario:</span>
                          <span className="font-black text-indigo-900 text-lg">
                            ${tokenComp.daily_projection_10k.savings_usd.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    )}

                    {tokenComp.monthly_projection_300k && (
                      <div className="bg-purple-50 p-4 rounded-xl border border-purple-200">
                        <p className="text-xs font-bold text-purple-700 uppercase mb-2">
                          Proyección a 300,000 reseñas/mes
                        </p>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-purple-700">Costo sin optimizar:</span>
                          <span className="font-bold text-purple-900">
                            ${tokenComp.monthly_projection_300k.cost_original_usd.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm mt-1">
                          <span className="text-purple-700">Costo optimizado:</span>
                          <span className="font-bold text-purple-900">
                            ${tokenComp.monthly_projection_300k.cost_translated_usd.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm mt-2 pt-2 border-t border-purple-300">
                          <span className="text-purple-700 font-bold">Ahorro mensual:</span>
                          <span className="font-black text-purple-900 text-lg">
                            ${tokenComp.monthly_projection_300k.savings_usd.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              )}
            </>
          ) : !mutation.isPending ? (
            <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center flex flex-col items-center justify-center min-h-[340px]">
              <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-base font-bold text-slate-800">Panel de Resultados</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-xs">
                Selecciona un archivo y ejecuta el análisis para ver métricas, tiempo de procesamiento y clasificación de errores.
              </p>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}