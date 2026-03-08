import { api } from '../api'
import { useFetch } from '../hooks'

export default function Products() {
  const { data: products, loading } = useFetch(() => api.listProducts(), [])

  if (loading) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-stone-400">
        Loading…
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-lg font-semibold text-stone-800">Products</h1>
      <p className="mt-1 text-sm text-stone-500">Catalog of available products.</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {(products ?? []).map((p) => (
          <div
            key={p.id}
            className="rounded-lg border border-stone-200 bg-white p-5"
            data-testid="product-card"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-sm font-medium text-stone-800">{p.name}</h3>
                <span className="mt-0.5 inline-block rounded-full bg-stone-100 px-2 py-0.5 text-[11px] font-medium text-stone-500">
                  {p.category}
                </span>
              </div>
              <span
                className={`inline-flex h-2 w-2 rounded-full ${p.is_active ? 'bg-emerald-400' : 'bg-stone-300'}`}
                title={p.is_active ? 'Active' : 'Inactive'}
              />
            </div>
            {p.description && (
              <p className="mt-2 text-xs text-stone-400 line-clamp-2">{p.description}</p>
            )}
            <div className="mt-4 flex items-baseline justify-between border-t border-stone-100 pt-3">
              <span className="text-lg font-semibold text-stone-800">
                ${p.price.toFixed(2)}
              </span>
              <span className="text-xs text-stone-400">
                {p.stock_quantity} in stock
              </span>
            </div>
          </div>
        ))}
        {(products ?? []).length === 0 && (
          <p className="col-span-full py-8 text-center text-sm text-stone-400">
            No products found.
          </p>
        )}
      </div>
    </div>
  )
}
