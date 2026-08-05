import React, { useState } from "react";
import { useBenchmark } from "@/hooks/useApi";
import Card from "@/components/ui/Card";

interface BenchmarkRow {
  file: string;
  total_records: number;
  total_time: number;
  tokens_original: number;
  cost_original: number;
  reviews_per_second: number;
}

export default function BenchmarkPage() {
  const mutation = useBenchmark();
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [history, setHistory] = useState<BenchmarkRow[]>([]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFileName(e.target.files[0].name);
    } else {
      setSelectedFileName(null);
    }
  };

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const fileInput = e.currentTarget.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;
    if (!fileInput.files || fileInput.files.length === 0) return;

    form.append("file", fileInput.files[0]);
    form.append("review_column", "reseña");
    form.append("optimize_tokens", "true");

    mutation.mutate(form, {
      onSuccess: (data) => {
        const row: BenchmarkRow = {
          file: data.file_path.split("/").pop() || data.file_path,
          total_records: data.total_records,
          total_time: data.totals.total_time_seconds,
          tokens_original: data.totals.tokens_original,
          cost_original: data.totals.cost_original_usd,
          reviews_per_second: data.totals.records_per_second_read,
        };
        setHistory((prev) => [row, ...prev]);
      },
    });
  };

  const data = mutation.data;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">
          Benchmark de Rendimiento
        </h1>
        <p className="text-slate-600 text-sm mt-1">
          Mide el tiempo real de procesamiento, tokenización y costos para cada
          archivo de reseñas.
        </p>
      </div>

      <Card title="Ejecutar Benchmark">
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Archivo Excel para Benchmark
            </label>
            <div className="relative border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-6 text-center bg-slate-50 transition-colors">
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="flex flex-col items-center justify-center space-y-2 pointer-events-none">
                {selectedFileName ? (
                  <p className="text-sm font-bold text-blue-600 bg-blue-50 px-3 py-1 rounded-md border border-blue-200">
                    📄 {selectedFileName}
                  </p>
                ) : (
                  <p className="text-sm font-semibold text-slate-700">
                    Selecciona un archivo .xlsx
                  </p>
                )}
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={mutation.isPending || !selectedFileName}
            className="w-full py-3 px-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold rounded-xl shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2"
          >
            {mutation.isPending ? (
              <>
                <svg
                  className="animate-spin h-5 w-5 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  ></path>
                </svg>
                <span>Ejecutando benchmark...</span>
              </>
            ) : (
              <span>🚀 Ejecutar Benchmark</span>
            )}
          </button>

          {mutation.isError && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
              <strong>Error:</strong> {(mutation.error as Error).message}
            </div>
          )}
        </form>
      </Card>

      {data && (
        <>
          <Card title="Resultados del Archivo Actual">
            <div className="space-y-6">
              {/* Resumen General */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-blue-50 p-4 rounded-xl text-center border border-blue-200">
                  <p className="text-xs font-bold text-blue-600 uppercase">
                    Registros
                  </p>
                  <p className="text-3xl font-black text-blue-900">
                    {data.total_records.toLocaleString()}
                  </p>
                </div>
                <div className="bg-emerald-50 p-4 rounded-xl text-center border border-emerald-200">
                  <p className="text-xs font-bold text-emerald-600 uppercase">
                    Tiempo Total
                  </p>
                  <p className="text-3xl font-black text-emerald-900">
                    {data.totals.total_time_seconds}s
                  </p>
                </div>
                <div className="bg-purple-50 p-4 rounded-xl text-center border border-purple-200">
                  <p className="text-xs font-bold text-purple-600 uppercase">
                    Registros/seg
                  </p>
                  <p className="text-3xl font-black text-purple-900">
                    {data.totals.records_per_second_read.toLocaleString()}
                  </p>
                </div>
                <div className="bg-amber-50 p-4 rounded-xl text-center border border-amber-200">
                  <p className="text-xs font-bold text-amber-600 uppercase">
                    Tokens/registro
                  </p>
                  <p className="text-3xl font-black text-amber-900">
                    {data.totals.tokens_per_record}
                  </p>
                </div>
              </div>

              {/* Desglose de Tiempos */}
              <div>
                <h4 className="text-xs font-bold uppercase text-slate-500 mb-3">
                  Desglose de Tiempos por Operación
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                  {Object.entries(data.timings).map(([key, value]) => (
                    <div
                      key={key}
                      className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-center"
                    >
                      <p className="text-[10px] font-bold text-slate-500 uppercase leading-tight">
                        {key.replace(/_/g, " ")}
                      </p>
                      <p className="text-lg font-black text-slate-900 mt-1">
                        {value}s
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Tokens y Costos */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                  <h4 className="text-xs font-bold uppercase text-slate-500 mb-3">
                    Tokens
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600">Originales:</span>
                      <span className="font-bold text-slate-900">
                        {data.totals.tokens_original.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Traducidos:</span>
                      <span className="font-bold text-blue-600">
                        {data.totals.tokens_translated.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between pt-2 border-t border-slate-200">
                      <span className="text-slate-600">Reducción:</span>
                      <span className="font-bold text-emerald-600">
                        {data.totals.percentage_reduction}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                  <h4 className="text-xs font-bold uppercase text-slate-500 mb-3">
                    Costos (USD)
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600">Sin optimizar:</span>
                      <span className="font-bold text-slate-900">
                        ${data.totals.cost_original_usd.toFixed(4)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Optimizado:</span>
                      <span className="font-bold text-blue-600">
                        ${data.totals.cost_translated_usd.toFixed(4)}
                      </span>
                    </div>
                    <div className="flex justify-between pt-2 border-t border-slate-200">
                      <span className="text-slate-600">Ahorro:</span>
                      <span className="font-bold text-emerald-600">
                        ${data.totals.cost_savings_usd.toFixed(4)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Proyecciones */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-200">
                  <h4 className="text-xs font-bold uppercase text-indigo-700 mb-2">
                    Proyección 10,000 reseñas/día
                  </h4>
                  <p className="text-sm text-indigo-700">
                    Tokens: <strong>{data.projections.daily_10k.tokens.toLocaleString()}</strong>
                  </p>
                  <p className="text-lg font-black text-indigo-900">
                    ${data.projections.daily_10k.cost_usd.toFixed(2)} /día
                  </p>
                </div>
                <div className="bg-purple-50 p-4 rounded-xl border border-purple-200">
                  <h4 className="text-xs font-bold uppercase text-purple-700 mb-2">
                    Proyección 300,000 reseñas/mes
                  </h4>
                  <p className="text-sm text-purple-700">
                    Tokens: <strong>{data.projections.monthly_300k.tokens.toLocaleString()}</strong>
                  </p>
                  <p className="text-lg font-black text-purple-900">
                    ${data.projections.monthly_300k.cost_usd.toFixed(2)} /mes
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </>
      )}

      {history.length > 0 && (
        <Card title={`Historial de Benchmarks (${history.length})`}>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500 uppercase text-xs border-b">
                <tr>
                  <th className="py-3 px-4 font-bold">Archivo</th>
                  <th className="py-3 px-4 font-bold">Registros</th>
                  <th className="py-3 px-4 font-bold">Tiempo Total</th>
                  <th className="py-3 px-4 font-bold">Tokens</th>
                  <th className="py-3 px-4 font-bold">Costo</th>
                  <th className="py-3 px-4 font-bold">Reg/seg</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="py-3 px-4 font-mono text-xs font-bold text-blue-600">
                      {row.file}
                    </td>
                    <td className="py-3 px-4 font-medium">
                      {row.total_records.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-bold text-emerald-600">
                      {row.total_time}s
                    </td>
                    <td className="py-3 px-4">
                      {row.tokens_original.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-medium">
                      ${row.cost_original.toFixed(4)}
                    </td>
                    <td className="py-3 px-4 font-bold text-purple-600">
                      {row.reviews_per_second.toLocaleString()}/s
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}