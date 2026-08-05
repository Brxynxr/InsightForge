import { Link } from "react-router-dom";
import { useHistory } from "@/hooks/useApi";
import Card from "@/components/ui/Card";

export default function DashboardPage() {
  const { data, isLoading } = useHistory();
  const history = data?.history || [];

  const totalJobs = history.length;
  const completedJobs = history.filter(
    (h) => h.status === "completed" || h.status === "completed_with_errors"
  ).length;

  const totalTokens = history.reduce(
    (acc, h) => acc + (h.total_tokens || h.metrics?.total_tokens || 0),
    0
  );

  const totalCost = history.reduce(
    (acc, h) => acc + (h.estimated_cost || h.metrics?.estimated_cost || 0),
    0
  );

  const totalRecordsProcessed = history.reduce(
    (acc, h) => acc + (h.total_records || 0),
    0
  );

  return (
    <div className="space-y-8">
      {/* Encabezado */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-blue-900 to-slate-900 text-white p-6 rounded-2xl shadow-lg">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Panel Principal de Control
          </h1>
          <p className="text-blue-200 text-sm mt-1">
            Gestión y monitoreo centralizado de optimización de prompts y datasets.
          </p>
        </div>
        <Link
          to="/upload"
          className="inline-flex items-center justify-center space-x-2 px-5 py-2.5 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-xl shadow-md transition-all transform hover:-translate-y-0.5"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>Nuevo Procesamiento</span>
        </Link>
      </div>

      {/* Tarjetas de Métricas Clave (KPIs) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Procesos Ejecutados</p>
            <p className="text-2xl font-black text-slate-900 mt-0.5">
              {isLoading ? "..." : totalJobs}
            </p>
            <p className="text-xs text-emerald-600 font-medium mt-0.5">
              {completedJobs} completados
            </p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Registros Procesados</p>
            <p className="text-2xl font-black text-slate-900 mt-0.5">
              {isLoading ? "..." : totalRecordsProcessed.toLocaleString()}
            </p>
            <p className="text-xs text-slate-500 font-medium mt-0.5">En datasets Excel/CSV</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Tokens Calculados</p>
            <p className="text-2xl font-black text-slate-900 mt-0.5">
              {isLoading ? "..." : totalTokens.toLocaleString()}
            </p>
            <p className="text-xs text-slate-500 font-medium mt-0.5">Tokenizador tiktoken o200k</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Costo Estimado</p>
            <p className="text-2xl font-black text-slate-900 mt-0.5">
              ${isLoading ? "..." : totalCost.toFixed(4)}
            </p>
            <p className="text-xs text-slate-500 font-medium mt-0.5">Basado en tarifas LLM</p>
          </div>
        </div>
      </div>

      {/* Acciones Rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/upload"
          className="group p-6 bg-white rounded-2xl border border-slate-200 hover:border-blue-500 shadow-sm hover:shadow-md transition-all"
        >
          <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center mb-4 group-hover:bg-blue-600 group-hover:text-white transition-colors">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
            Cargar y Procesar Archivo
          </h3>
          <p className="text-sm text-slate-600 mt-1">
            Sube un archivo de Excel (.xlsx) o CSV para traducirlo, calcular tokens y pasarlo a la IA.
          </p>
        </Link>

        <Link
          to="/history"
          className="group p-6 bg-white rounded-2xl border border-slate-200 hover:border-indigo-500 shadow-sm hover:shadow-md transition-all"
        >
          <div className="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center mb-4 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
            Historial de Ejecuciones
          </h3>
          <p className="text-sm text-slate-600 mt-1">
            Inspecciona resultados detallados de ejecuciones pasadas, exporta respuestas y revisa registros.
          </p>
        </Link>

        <Link
          to="/settings"
          className="group p-6 bg-white rounded-2xl border border-slate-200 hover:border-purple-500 shadow-sm hover:shadow-md transition-all"
        >
          <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mb-4 group-hover:bg-purple-600 group-hover:text-white transition-colors">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-slate-900 group-hover:text-purple-600 transition-colors">
            Ajustes y Proveedores
          </h3>
          <p className="text-sm text-slate-600 mt-1">
            Configura tus claves de API (OpenAI), idiomas de destino por defecto y parámetros del sistema.
          </p>
        </Link>
      </div>

      {/* Actividad Reciente */}
      <Card title="Últimos Procesos Ejecutados">
        {isLoading ? (
          <p className="text-center py-6 text-slate-500">Cargando historial...</p>
        ) : history.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            <p className="mb-3">Aún no se ha realizado ningún procesamiento de archivos.</p>
            <Link
              to="/upload"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700"
            >
              Comenzar primer proceso
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 uppercase text-xs border-b">
                <tr>
                  <th className="py-3 px-4">Batch ID</th>
                  <th className="py-3 px-4">Archivo</th>
                  <th className="py-3 px-4">Estado</th>
                  <th className="py-3 px-4">Registros</th>
                  <th className="py-3 px-4">Tokens</th>
                  <th className="py-3 px-4">Costo Estimado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.slice(0, 5).map((item) => (
                  <tr key={item.batch_id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-blue-600 font-semibold">
                      {item.batch_id.slice(0, 8)}...
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-800">
                      {item.file_name || "Archivo de Excel"}
                    </td>
                    <td className="py-3 px-4">
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
                    <td className="py-3 px-4 text-slate-600">{item.total_records || 0}</td>
                    <td className="py-3 px-4 text-slate-600">
                      {(item.total_tokens || item.metrics?.total_tokens || 0).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-800">
                      ${(item.estimated_cost || item.metrics?.estimated_cost || 0).toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}