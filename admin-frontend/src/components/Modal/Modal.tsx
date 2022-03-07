import { createContext, useContext, useEffect, useRef } from 'react';

interface ModalContextType {
  onClose: () => void;
}

const ModalContext = createContext<ModalContextType>({
  onClose: () => { },
});

interface ModalProps {
  show: boolean;
  onClose: () => void;
}

const Modal: React.FunctionComponent<ModalProps> = ({ show, onClose, children }) => {
  const elementRef = useRef<HTMLDivElement>(null);

  // Outside click
  useEffect(() => {
    const clickHandler = ({ target }: MouseEvent) => {
      if (!target || !elementRef.current) return;
      console.log(show, elementRef.current, target);
      if (!show || elementRef.current.contains(target as Node)) return;
      onClose();
    };
    document.addEventListener('click', clickHandler);
    return () => document.removeEventListener('click', clickHandler);
  });

  // Esc key
  useEffect(() => {
    const keyHandler = ({ code }: KeyboardEvent) => {
      if (!show || code !== 'Escape') return;
      onClose();
    };
    document.addEventListener('keydown', keyHandler);
    return () => document.removeEventListener('keydown', keyHandler);
  });

  return (
    <>
      {show && <div className="fixed inset-0 bg-slate-900 bg-opacity-30 z-30"></div>}
      {show &&
        <div
          className="fixed inset-0 z-30 overflow-hidden flex items-center my-4 justify-center transform px-4 sm:px-6"
          role="dialog"
          aria-modal="true"
        >
          <div ref={elementRef} className="bg-white rounded shadow-lg overflow-auto max-w-lg w-full max-h-full">
            <ModalContext.Provider value={{ onClose }}>
              {children}
            </ModalContext.Provider>
          </div>
        </div>
      }
    </>
  );
};

interface ModalHeaderProps {
  closeButton?: boolean;
}

const ModalHeader: React.FunctionComponent<ModalHeaderProps> = ({ children, closeButton }) => {
  const { onClose } = useContext(ModalContext);

  return (
    <div className="px-5 py-3 border-b border-slate-200">
      <div className="flex justify-between items-center">
        {children}
        {closeButton &&
          <button className="text-slate-400 hover:text-slate-500" onClick={() => onClose()}>
            <div className="sr-only">Close</div>
            <svg className="w-4 h-4 fill-current">
              <path d="M7.95 6.536l4.242-4.243a1 1 0 111.415 1.414L9.364 7.95l4.243 4.242a1 1 0 11-1.415 1.415L7.95 9.364l-4.243 4.243a1 1 0 01-1.414-1.415L6.536 7.95 2.293 3.707a1 1 0 011.414-1.414L7.95 6.536z" />
            </svg>
          </button>
        }
      </div>
    </div>
  )
};

ModalHeader.defaultProps = {
  closeButton: false,
};

const ModalTitle: React.FunctionComponent = ({ children }) => {
  return (
    <div className="font-semibold text-slate-800">{children}</div>
  )
};

const ModalBody: React.FunctionComponent = ({ children }) => {
  return (
    <div className="p-5">
      {children}
    </div>
  )
};

const ModalFooter: React.FunctionComponent = ({ children }) => {
  return (
    <div className="p-5 p-5 flex flex-wrap justify-end space-x-2">
      {children}
    </div>
  )
};

const Components = Object.assign(Modal, {
  Header: ModalHeader,
  Title: ModalTitle,
  Body: ModalBody,
  Footer: ModalFooter,
});

export default Components;
