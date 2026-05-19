import { useEffect } from 'react'

export default function Toast({ toasts, remove }) {
  return (
    <div className="toast-wrap">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} remove={remove} />
      ))}
    </div>
  )
}

function ToastItem({ toast, remove }) {
  useEffect(() => {
    const timer = setTimeout(() => remove(toast.id), 3500)
    return () => clearTimeout(timer)
  }, [toast.id, remove])

  const icon = toast.type === 'success' ? '✓' : toast.type === 'error' ? '✕' : 'ℹ'

  return (
    <div className={`toast ${toast.type}`} onClick={() => remove(toast.id)}>
      <span>{icon}</span>
      <span>{toast.message}</span>
    </div>
  )
}
