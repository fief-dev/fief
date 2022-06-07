import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Popover, Transition } from '@headlessui/react';
import { EyeIcon, EyeOffIcon, SelectorIcon, ViewListIcon } from '@heroicons/react/solid';
import { useCallback, useContext, useState } from 'react';
import { usePopper } from 'react-popper';

import UserFieldsSelectionContext, { UserFieldSelection } from '../../contexts/user-fields-selection';

interface UserFieldsSelectorItemProps {
  id: string;
  userField: UserFieldSelection;
  onToggle: (userField: UserFieldSelection, enabled: boolean) => void;
}

interface UserFieldsSelectorProps {
}

const UserFieldsSelectorItem: React.FunctionComponent<React.PropsWithChildren<UserFieldsSelectorItemProps>> = ({ id, userField, onToggle }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      className="p-1 flex flex-row items-center justify-between select-none text-sm rounded hover:bg-slate-100"
      ref={setNodeRef}
      style={style}
      {...attributes}
    >
      <div className="flex flex-row items-center grow" {...listeners}>
        <SelectorIcon width="12" height="12" className="mr-1" />
        {userField.name}
      </div>
      {userField.enabled &&
        <EyeIcon width="12" height="12" className="cursor-pointer" onClick={() => onToggle(userField, false)} />
      }
      {!userField.enabled &&
        <EyeOffIcon width="12" height="12" className="cursor-pointer" onClick={() => onToggle(userField, true)} />
      }
    </div>
  );
};

const UserFieldsSelector: React.FunctionComponent<React.PropsWithChildren<UserFieldsSelectorProps>> = () => {
  const [userFieldsSelection, setUserFieldsSelection] = useContext(UserFieldsSelectionContext);

  let [referenceElement, setReferenceElement] = useState<HTMLButtonElement | null>();
  let [popperElement, setPopperElement] = useState<HTMLDivElement | null>();
  let { styles, attributes } = usePopper(referenceElement, popperElement, { placement: 'bottom-end' });

  const toggleUserField = useCallback((toggledUserField: UserFieldSelection, enabled: boolean) => {
    const updated: UserFieldSelection[] = [];
    for (const userField of userFieldsSelection) {
      if (userField.id === toggledUserField.id) {
        updated.push({ ...userField, enabled });
      } else {
        updated.push(userField);
      }
    }
    setUserFieldsSelection(updated);
  }, [userFieldsSelection, setUserFieldsSelection]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setUserFieldsSelection((items) => {
        const oldIndex = items.findIndex((userField) => userField.id === active.id)
        const newIndex = items.findIndex((userField) => userField.id === over.id)

        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  return (
    <Popover className="flex">
      <Popover.Button
        ref={setReferenceElement}
        className="btn bg-white border-slate-200 hover:border-slate-300 text-slate-500 hover:text-slate-600"
      >
        <ViewListIcon width="16" height="16" />
      </Popover.Button>

      <div
        ref={setPopperElement}
        style={styles.popper}
        {...attributes.popper}
        className="z-10"
      >
        <Transition
          enter="transition duration-100 ease-out"
          enterFrom="transform scale-95 opacity-0"
          enterTo="transform scale-100 opacity-100"
          leave="transition duration-75 ease-out"
          leaveFrom="transform scale-100 opacity-100"
          leaveTo="transform scale-95 opacity-0"
        >
          <Popover.Panel
            className="mt-1 bg-white rounded shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none w-40 p-1"
          >
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={userFieldsSelection}
                strategy={verticalListSortingStrategy}
              >
                {userFieldsSelection.map((userField) =>
                  <UserFieldsSelectorItem
                    key={userField.id}
                    id={userField.id}
                    userField={userField}
                    onToggle={toggleUserField}
                  />
                )}
              </SortableContext>
            </DndContext>
          </Popover.Panel>
        </Transition>
      </div>
    </Popover>
  );
};

export default UserFieldsSelector;
