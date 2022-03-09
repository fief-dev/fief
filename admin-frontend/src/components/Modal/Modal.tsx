import React, { createContext, Fragment, useContext } from 'react';
import { Dialog, Transition } from '@headlessui/react'
import { XIcon } from '@heroicons/react/solid';

interface ModalContextType {
  onClose: () => void;
}

const ModalContext = createContext<ModalContextType>({
  onClose: () => { },
});

interface ModalProps {
  open: boolean;
  onClose: () => void;
}

const Modal: React.FunctionComponent<ModalProps> = ({ open, onClose, children }) => {
  return (
    <Transition appear show={open} as={Fragment}>
      <Dialog
        as="div"
        className="fixed inset-0 z-10 overflow-y-auto"
        onClose={onClose}
      >
        <div className="min-h-screen px-4 text-center">
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <Dialog.Overlay className="fixed inset-0 bg-slate-900 bg-opacity-30" />
          </Transition.Child>

          {/* This element is to trick the browser into centering the modal contents. */}
          <span
            className="inline-block h-screen align-middle"
            aria-hidden="true"
          >
            &#8203;
          </span>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <div className="inline-block w-full max-w-md overflow-hidden text-left align-middle transition-all transform bg-white rounded shadow-lg">
              <ModalContext.Provider value={{ onClose }}>
                {children}
              </ModalContext.Provider>
            </div>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition>
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
          <button type="button" className="text-slate-400 hover:text-slate-500" onClick={() => onClose()}>
            <div className="sr-only">Close</div>
            <XIcon className="w-4 h-4 fill-current" />
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
    <Dialog.Title className="font-semibold text-slate-800">{children}</Dialog.Title>
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
