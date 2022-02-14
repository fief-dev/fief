import React, { Dispatch, useEffect, useState } from 'react';

export const useToggle = (triggerRef: React.MutableRefObject<any>, elementRef: React.MutableRefObject<any>, shown: boolean = false): [boolean, Dispatch<boolean>] => {
  const [show, setShow] = useState<boolean>(shown);

  // Outside click
  useEffect(() => {
    const clickHandler = ({ target }: MouseEvent) => {
      if (!target || !elementRef.current || !triggerRef.current) return;
      if (!show || elementRef.current.contains(target as Node) || triggerRef.current.contains(target as Node)) return;
      setShow(false);
    };
    document.addEventListener('click', clickHandler);
    return () => document.removeEventListener('click', clickHandler);
  });

  // Esc key
  useEffect(() => {
    const keyHandler = ({ code }: KeyboardEvent) => {
      if (!show || code !== 'Escape') return;
      setShow(false);
    };
    document.addEventListener('keydown', keyHandler);
    return () => document.removeEventListener('keydown', keyHandler);
  });

  return [show, setShow];
}
