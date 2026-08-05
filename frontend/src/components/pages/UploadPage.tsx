import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link } from "react-router-dom";
import { useProcessJob } from "@/hooks/useApi";
import { useAppStore } from "@/stores/appStore";
import Card from "@/components/ui/Card";
import MetricsDisplay from "@/components/ui/MetricsDisplay";

const schema = z.object({
  file: z
    .custom<FileList>()
    .refine((files) => files && files.length > 0, "Se requiere seleccionar un archivo Excel o CSV"),
  required_columns: z.string().optional(),
  target_language: z.string().optional(),
  export_formats: z.string().optional(),
});

type Schema = z.infer<typeof schema>;

export default function UploadPage() {
  const mutation = useProcessJob();
  const settings = useAppStore((state) => state.settings);
  const setSettings = useAppStore((state) => state.updateSettings);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Schema>({
    resolver: zodResolver(schema),
    defaultValues: {
      target_language: settings.target_language || "es",
      export_formats: "json,excel,csv",
    },
  });

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
    if (data.required_columns) {
      formData.append("required_columns", data.required_columns);
    }
    formData.append("target_language", data.target_language || "es");
    if (data.export_formats) {
      formData.append("export_formats", data.export_formats);
    }

    setSettings({
      target_language: data.target_language || "es",
      export_formats: data.export_formats
        ? data.export_formats.split(",")
        : ["json"],
    });

    mutation.mutate(formData);
  };

  return (
    <div className="space-y-8">
      {/* Encabezado */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">
          Procesamiento y Carga de Archivos
        </h1>
        <p className="text-slate-600 text-sm mt-1">
          Sube tu conjunto de datos en Excel o CSV para ejecutar el pipeline de traducción, conteo de tokens y evaluación por IA.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Formulario de Carga */}
        <div className="lg:col-span-7">
          <Card title="1. Configuración del Archivo">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Zona de Drop/Archivo */}
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Archivo de Entrada (Excel / CSV)
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
                          Formatos soportados: .xlsx, .xls, .csv
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

              {/* Columnas Requeridas */}
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">
                  Columnas Requeridas (Opcional)
                </label>
                <p className="text-xs text-slate-500 mb-2">
                  Ingresa los nombres de las columnas que deben estar presentes (separadas por coma). Ejemplo: <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">text,categoria</code>
                </p>
                <input
                  type="text"
                  placeholder="ej: text, prompt, descripcion"
                  {...register("required_columns")}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>

              {/* Idioma Objetivo */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1">
                    Idioma Objetivo
                  </label>
                  <select
                    {...register("target_language")}
                    className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  >
                    <option value="es">Español (es)</option>
                    <option value="en">Inglés (en)</option>
                    <option value="pt">Portugués (pt)</option>
                    <option value="fr">Francés (fr)</option>
                    <option value="de">Alemán (de)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1">
                    Formatos de Exportación
                  </label>
                  <input
                    type="text"
                    placeholder="json,excel,csv"
                    {...register("export_formats")}
                    className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Botón Acción */}
              <button
                type="submit"
                disabled={mutation.isPending || !selectedFileName}
                className="w-full py-3.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold rounded-xl shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2"
              >
                {mutation.isPending ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Ejecutando Pipeline de Procesamiento...</span>
                  </>
                ) : (
                  <span>Iniciar Procesamiento de Archivo</span>
                )}
              </button>

              {mutation.isError && (
                <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
                  <strong>Error de Ejecución:</strong> {(mutation.error as Error).message}
                </div>
              )}
            </form>
          </Card>
        </div>

        {/* Panel de Resultados Inmediatos */}
        <div className="lg:col-span-5">
          {mutation.data ? (
            <Card title="2. Resultados del Procesamiento">
              <div className="space-y-6">
                {/* Banner de Estado */}
                <div
                  className={`p-4 rounded-xl border flex items-center justify-between ${
                    mutation.data.status === "completed"
                      ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                      : "bg-amber-50 border-amber-200 text-amber-900"
                  }`}
                >
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider">Estado del Proceso</p>
                    <p className="text-lg font-black mt-0.5">
                      {mutation.data.status === "completed"
                        ? "✅ Completado Exitosamente"
                        : "⚠️ Completado con Advertencias"}
                    </p>
                  </div>
                  <span className="text-xs font-mono bg-white px-2.5 py-1 rounded-md border shadow-sm">
                    {mutation.data.batch_id.slice(0, 8)}...
                  </span>
                </div>

                {/* Métricas */}
                <div>
                  <h4 className="text-xs font-bold uppercase text-slate-500 tracking-wider mb-3">
                    Métricas Calculadas
                  </h4>
                  <MetricsDisplay metrics={mutation.data.metrics} />
                </div>

                {/* Vista previa de Resultados */}
                {mutation.data.results && mutation.data.results.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold uppercase text-slate-500 tracking-wider mb-2">
                      Muestra de Respuestas del Modelo
                    </h4>
                    <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                      {mutation.data.results.slice(0, 3).map((r, i) => (
                        <div
                          key={i}
                          className="bg-slate-900 text-slate-200 text-xs p-3 rounded-xl font-mono overflow-x-auto shadow-inner"
                        >
                          <span className="text-blue-400 font-bold block mb-1">Registro #{i + 1}</span>
                          <pre>{JSON.stringify(r, null, 2)}</pre>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="pt-2 flex flex-col space-y-2">
                  <Link
                    to="/history"
                    className="w-full text-center py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm rounded-xl transition-colors"
                  >
                    Ver en el Historial Completo
                  </Link>
                </div>
              </div>
            </Card>
          ) : (
            <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center flex flex-col items-center justify-center min-h-[340px]">
              <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              </div>
              <h3 className="text-base font-bold text-slate-800">Panel de Resultados</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-xs">
                Selecciona y procesa un archivo a la izquierda para visualizar aquí las métricas en tiempo real.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}