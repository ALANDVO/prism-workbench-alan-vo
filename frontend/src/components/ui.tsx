import React from 'react'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-[2px]',
    md: 'w-6 h-6 border-[2px]',
    lg: 'w-8 h-8 border-[3px]',
  }

  return (
    <div
      className={`${sizeClasses[size]} border-[var(--color-border)] border-t-[var(--color-primary)] rounded-full animate-spin ${className}`}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  )
}

interface EmptyStateProps {
  icon: React.ReactNode
  title: string
  description: string
  action?: React.ReactNode
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon" aria-hidden="true">{icon}</div>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-description">{description}</p>
      {action && <div>{action}</div>}
    </div>
  )
}

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const variantClasses = {
    primary: 'btn btn-primary',
    secondary: 'btn btn-secondary',
    danger: 'btn btn-danger',
    ghost: 'btn btn-ghost',
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  }

  return (
    <button
      className={`${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner size={size === 'lg' ? 'md' : 'sm'} className="mr-2" />}
      {children}
    </button>
  )
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export function Input({ label, error, className = '', id, ...props }: InputProps) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="label">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`input ${className} ${error ? 'border-[var(--color-error)]' : ''}`}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={error ? `${inputId}-error` : undefined}
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="text-sm text-[var(--color-error)] mt-1">
          {error}
        </p>
      )}
    </div>
  )
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  placeholder?: string
  options: Array<{ value: string; label: string }>
  error?: string
}

export function Select({ label, placeholder, options, error, className = '', id, ...props }: SelectProps) {
  const selectId = id || label?.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={selectId} className="label">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`input ${className} ${error ? 'border-[var(--color-error)]' : ''}`}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={error ? `${selectId}-error` : undefined}
        {...props}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <p id={`${selectId}-error`} className="text-sm text-[var(--color-error)] mt-1">
          {error}
        </p>
      )}
    </div>
  )
}

interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return <div className={`card ${className}`}>{children}</div>
}

interface BadgeProps {
  children: React.ReactNode
  variant?: 'primary' | 'success' | 'warning' | 'error' | 'secondary'
  className?: string
}

export function Badge({ children, variant = 'secondary', className = '' }: BadgeProps) {
  const variantClasses = {
    primary: 'badge badge-primary',
    success: 'badge badge-success',
    warning: 'badge badge-warning',
    error: 'badge badge-error',
    secondary: 'badge badge-secondary',
  }

  return (
    <span className={`${variantClasses[variant]} ${className}`}>{children}</span>
  )
}

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  className?: string
}

export function Pagination({ currentPage, totalPages, onPageChange, className = '' }: PaginationProps) {
  if (totalPages <= 1) return null

  const pages = Array.from({ length: totalPages }, (_, i) => i + 1)
  const maxVisiblePages = 5

  let visiblePages: number[]
  if (totalPages <= maxVisiblePages) {
    visiblePages = pages
  } else {
    const half = Math.floor(maxVisiblePages / 2)
    let start = Math.max(1, currentPage - half)
    let end = Math.min(totalPages, start + maxVisiblePages - 1)

    if (end - start + 1 < maxVisiblePages) {
      start = Math.max(1, end - maxVisiblePages + 1)
    }

    visiblePages = pages.slice(start - 1, end)
  }

  return (
    <nav className={`flex items-center justify-center gap-1 ${className}`} aria-label="Pagination">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="btn btn-secondary px-3 py-1.5"
        aria-label="Previous page"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      {visiblePages[0] > 1 && (
        <>
          <button
            onClick={() => onPageChange(1)}
            className="btn btn-secondary px-3 py-1.5"
            aria-label="Page 1"
          >
            1
          </button>
          {visiblePages[0] > 2 && (
            <span className="px-2 text-[var(--color-text-muted)]">...</span>
          )}
        </>
      )}

      {visiblePages.map((page) => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={`btn ${page === currentPage ? 'btn-primary' : 'btn-secondary'} px-3 py-1.5`}
          aria-label={`Page ${page}`}
          aria-current={page === currentPage ? 'page' : undefined}
        >
          {page}
        </button>
      ))}

      {visiblePages[visiblePages.length - 1] < totalPages && (
        <>
          {visiblePages[visiblePages.length - 1] < totalPages - 1 && (
            <span className="px-2 text-[var(--color-text-muted)]">...</span>
          )}
          <button
            onClick={() => onPageChange(totalPages)}
            className="btn btn-secondary px-3 py-1.5"
            aria-label={`Page ${totalPages}`}
          >
            {totalPages}
          </button>
        </>
      )}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="btn btn-secondary px-3 py-1.5"
        aria-label="Next page"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </nav>
  )
}
