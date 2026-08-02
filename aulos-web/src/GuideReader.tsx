import { useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { GUIDE_IFRAME_SANDBOX, prepareGuideHtml } from './guideHtml'

type Props = {
  html: string
  title: string
  className?: string
  fullscreenLabel?: string
  exitLabel?: string
}

/**
 * Guide iframe + in-app immersive reader for travel / one-hand browsing.
 * Prefer this over opening a blob tab (hard to return on mobile).
 */
export function GuideReader({
  html,
  title,
  className = '',
  fullscreenLabel = '全屏阅读',
  exitLabel = '退出全屏',
}: Props) {
  const [immersive, setImmersive] = useState(false)
  const closeBtnRef = useRef<HTMLButtonElement>(null)
  const shellRef = useRef<HTMLDivElement>(null)
  const titleId = useId()
  const srcDoc = prepareGuideHtml(html)

  useEffect(() => {
    if (!immersive) return
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeBtnRef.current?.focus()

    const shell = shellRef.current
    const tryFs = async () => {
      if (!shell || document.fullscreenElement) return
      try {
        await shell.requestFullscreen?.()
      } catch {
        /* iOS Safari often blocks — CSS immersive still works */
      }
    }
    void tryFs()

    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setImmersive(false)
    }
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = prevOverflow
      window.removeEventListener('keydown', onKey)
      if (document.fullscreenElement) {
        void document.exitFullscreen().catch(() => undefined)
      }
    }
  }, [immersive])

  return (
    <div className={`guide-reader ${className}`.trim()}>
      <div className="guide-reader-bar">
        <p className="guide-reader-bar-hint">正文已铺满阅读区；需要时可进入专注模式</p>
        <button
          type="button"
          className="btn btn-ghost btn-sm guide-reader-enter"
          onClick={() => setImmersive(true)}
        >
          {fullscreenLabel}
        </button>
      </div>
      <iframe className="guide-frame" title={title} sandbox={GUIDE_IFRAME_SANDBOX} srcDoc={srcDoc} />

      {immersive
        ? createPortal(
            <div
              ref={shellRef}
              className="guide-reader-immersive"
              role="dialog"
              aria-modal="true"
              aria-labelledby={titleId}
            >
              <header className="guide-reader-immersive-head">
                <div className="guide-reader-immersive-titles">
                  <p id={titleId} className="guide-reader-immersive-title">
                    {title}
                  </p>
                  <p className="guide-reader-immersive-hint">滑动阅读 · Esc / 右上角退出</p>
                </div>
                <button
                  ref={closeBtnRef}
                  type="button"
                  className="btn btn-primary guide-reader-exit"
                  onClick={() => setImmersive(false)}
                >
                  {exitLabel}
                </button>
              </header>
              <iframe
                className="guide-frame guide-reader-immersive-frame"
                title={`${title} · 全屏`}
                sandbox={GUIDE_IFRAME_SANDBOX}
                srcDoc={srcDoc}
              />
            </div>,
            document.body,
          )
        : null}
    </div>
  )
}
