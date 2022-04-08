import { QuestionMarkCircleIcon } from '@heroicons/react/solid';
import { Popover, Transition } from '@headlessui/react';
import { useState } from 'react';
import { usePopper } from 'react-popper';

interface TooltipProps {

}

const Tooltip: React.FunctionComponent<TooltipProps> = ({ children }) => {
  const [open, setOpen] = useState(false);
  const [referenceElement, setReferenceElement] = useState<HTMLDivElement | null>();
  const [popperElement, setPopperElement] = useState<HTMLDivElement | null>();
  const { styles, attributes } = usePopper(
    referenceElement,
    popperElement,
    {
      placement: 'right-start',
      modifiers: [
        { name: 'offset', options: { offset: [-10, 5] } },
      ]
    },
  );

  return (
    <Popover className="relative">
      <div
        ref={setReferenceElement}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
      >
        <QuestionMarkCircleIcon
          className="w-4 h-4 shrink-0 fill-current text-slate-400 mt-[3px]"
        />
      </div>
      <div
        ref={setPopperElement}
        style={styles.popper}
        {...attributes.popper}>
        <Transition

          enter="transition duration-100 ease-out"
          enterFrom="transform scale-95 opacity-0"
          enterTo="transform scale-100 opacity-100"
          leave="transition duration-75 ease-out"
          leaveFrom="transform scale-100 opacity-100"
          leaveTo="transform scale-95 opacity-0"
          show={open}
        >
          <Popover.Panel>
            <div className="rounded overflow-hidden bg-white border border-slate-200 shadow-lg p-1 text-xs z-10 w-96 whitespace-normal">
              {children}
            </div>
          </Popover.Panel>
        </Transition>
      </div>
    </Popover>
  );
};

export default Tooltip;
