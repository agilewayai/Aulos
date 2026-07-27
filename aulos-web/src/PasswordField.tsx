import { useState } from 'react'
import type { InputHTMLAttributes } from 'react'

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  /** Accessible name for the reveal control (default: password). */
  secretLabel?: string
}

/** Password / secret input with show/hide toggle. */
export function PasswordField({ secretLabel = 'password', className, disabled, ...rest }: Props) {
  const [visible, setVisible] = useState(false)
  const label = visible ? `Hide ${secretLabel}` : `Show ${secretLabel}`

  return (
    <div className={['password-field', className].filter(Boolean).join(' ')}>
      <input {...rest} type={visible ? 'text' : 'password'} disabled={disabled} />
      <button
        type="button"
        className="password-toggle"
        onClick={() => setVisible((v) => !v)}
        disabled={disabled}
        aria-label={label}
        aria-pressed={visible}
        title={label}
      >
        {visible ? 'Hide' : 'Show'}
      </button>
    </div>
  )
}
