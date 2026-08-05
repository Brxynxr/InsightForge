import { useState } from "react";
import { useHistory, useJobDetail } from "@/hooks/useApi";
import Card from "@/components/ui/Card";

export default function HistoryPage() {
  const { data, isLoading, refetch } = useHistory();
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const { data: detailData, isLoading: detailLoading } = useJobDetail(selectedBatchId);

  const history = data?.history || [];

  const filteredHistory = history.filter(
    (item) =>
      item.batch_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.file_name && item.file_name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-8">
      {/* Encabezado */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Historial de Ejecuciones
          </h1>
          <p className="text-slate-600 text-sm mt-1">
            Consulta los detalles, métricas y resultados de todos los archivos procesados en el sistema.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold rounded-xl shadow-sm transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Actualizar</span>
        </button>
      </div>

      {/* Filtro de Búsqueda */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-3">
        <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          placeholder="Buscar por ID de Proceso o Nombre de Archivo..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full text-sm outline-none text-slate-800 placeholder-slate-400"
        />
      </div>

      {/* Tabla Principal */}
      <Card title={`Procesos Registrados (${filteredHistory.length})`}>
        {isLoading ? (
          <p className="text-center py-10 text-slate-500">Cargando historial desde la base de datos...</p>
        ) : filteredHistory.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <p className="text-base font-semibold">No se encontraron procesos registrados.</p>
            <p className="text-xs text-slate-400 mt-1">
              {searchTerm ? "Prueba cambiando el término de búsqueda." : "Ejecuta un nuevo procesamiento desde el menú de Cargar Archivo."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500 uppercase text-xs border-b">
                <tr>
                  <th className="py-3.5 px-4 font-bold">Batch ID</th>
                  <th className="py-3.5 px-4 font-bold">Archivo</th>
                  <th className="py-3.5 px-4 font-bold">Estado</th>
                  <th className="py-3.5 px-4 font-bold">Registros Validados</th>
                  <th className="py-3.5 px-4 font-bold">Tokens</th>
                  <th className="py-3.5 px-4 font-bold">Costo Est.</th>
                  <th className="py-3.5 px-4 font-bold text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredHistory.map((item) => (
                  <tr key={item.batch_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-mono text-xs text-blue-600 font-bold">
                      {item.batch_id.slice(0, 8)}...
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-900">
                      {item.file_name || "Excel dataset"}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          item.status === "completed"
                            ? "bg-emerald-100 text-emerald-800"
                            : item.status === "completed_with_errors"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-rose-100 text-rose-800"
                        }`}
                      >
                        {item.status === "completed"
                          ? "Completado"
                          : item.status === "completed_with_errors"
                          ? "Con Advertencias"
                          : item.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      {item.validated_records || 0} / {item.total_records || 0}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      {(item.total_tokens || item.metrics?.total_tokens || 0).toLocaleString()}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-900">
                      ${(item.estimated_cost || item.metrics?.estimated_cost || 0).toFixed(4)}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => setSelectedBatchId(item.batch_id)}
                        className="px-3 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-600 hover:text-white text-xs font-bold rounded-lg transition-colors"
                      >
                        Ver Detalle
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal / Drawer para Detalle de Trabajo */}
      {selectedBatchId && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Header del Modal */}
            <div className="bg-slate-900 text-white p-5 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold">Detalle del Proceso</h3>
                <p className="text-xs font-mono text-blue-400 mt-0.5">{selectedBatchId}</p>
              </div>
              <button
                onClick={() => setSelectedBatchId(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Contenido del Modal */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1">
              {detailLoading ? (
                <p className="text-center py-12 text-slate-500">Cargando registros detallados...</p>
              ) : detailData ? (
                <>
                  {/* Resumen del Trabajo */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
                    <div>
                      <p className="text-xs font-bold uppercase text-slate-500">Estado</p>
                      <p className="text-sm font-semibold text-slate-900 mt-0.5">{detailData.job.status}</p>
                    </div>
                    <div>
                      <p className="text-xs font-bold uppercase text-slate-500">Idioma Destino</p>
                      <p className="text-sm font-semibold text-slate-900 mt-0.5">{detailData.job.target_language || "es"}</p>
                    </div>
                    <div>
                      <p className="text-xs font-bold uppercase text-slate-500">Total Tokens</p>
                      <p className="text-sm font-semibold text-slate-900 mt-0.5">
                        {(detailData.job.total_tokens || 0).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-bold uppercase text-slate-500">Costo Estimado</p>
                      <p className="text-sm font-semibold text-slate-900 mt-0.5">
                        ${(detailData.job.estimated_cost || 0).toFixed(4)}
                      </p>
                    </div>
                  </div>

                  {/* Lista de Registros Procesados */}
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 mb-3">
                      Registros Individuales ({detailData.records.length})
                    </h4>
                    <div className="space-y-4">
                      {detailData.records.map((rec) => (
                        <div
                          key={rec.record_index}
                          className="p-4 bg-white border border-slate-200 rounded-xl space-y-2 shadow-sm"
                        >
                          <div className="flex items-center justify-between border-b pb-2">
                            <span className="text-xs font-bold text-blue-600">
                              Registro #{rec.record_index + 1}
                            </span>
                            <span className="text-xs font-medium text-slate-500">
                              Tokens: {rec.token_count}
                            </span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                            <div>
                              <strong className="text-slate-700 block mb-1">Texto Optimizado/Traducido:</strong>
                              <p className="bg-slate-50 p-2.5 rounded-lg text-slate-800 border">
                                {rec.optimized_text || JSON.stringify(rec.original_data)}
                              </p>
                            </div>

                            <div>
                              <strong className="text-slate-700 block mb-1">Respuesta del Modelo IA:</strong>
                              <p className="bg-slate-900 text-slate-100 p-2.5 rounded-lg font-mono border">
                                {rec.llm_response || (rec.error ? `Error: ${rec.error}` : JSON.stringify(rec.parsed_result))}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <p className="text-center text-rose-600">No se pudieron cargar los detalles del proceso.</p>
              )}
            </div>

            {/* Footer Modal */}
            <div className="bg-slate-50 border-t p-4 text-right">
              <button
                onClick={() => setSelectedBatchId(null)}
                className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}