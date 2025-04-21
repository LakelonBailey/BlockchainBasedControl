import { useState, useCallback } from "react";

interface UseDisclosureOptions {
  defaultIsOpen?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
  onToggle?: (isOpen: boolean) => void;
}

interface UseDisclosureReturn {
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  onToggle: () => void;
  getButtonProps: <T extends object>(props?: T) => T & { onClick: () => void };
  getDisclosureProps: <T extends object>(
    props?: T
  ) => T & { open: boolean; onClose: () => void };
}

function useDisclosure({
  defaultIsOpen = false,
  onOpen: onOpenProp,
  onClose: onCloseProp,
  onToggle: onToggleProp,
}: UseDisclosureOptions = {}): UseDisclosureReturn {
  const [isOpen, setIsOpen] = useState(defaultIsOpen);

  const onOpen = useCallback(() => {
    setIsOpen(true);
    if (onOpenProp) {
      onOpenProp();
    }
  }, [onOpenProp]);

  const onClose = useCallback(() => {
    setIsOpen(false);
    if (onCloseProp) {
      onCloseProp();
    }
  }, [onCloseProp]);

  const onToggle = useCallback(() => {
    setIsOpen((prev) => {
      const newState = !prev;
      if (onToggleProp) {
        onToggleProp(newState);
      }
      return newState;
    });
  }, [onToggleProp]);

  const getButtonProps = useCallback(
    <T extends object>(props: T = {} as T): T & { onClick: () => void } => ({
      ...props,
      onClick: onToggle,
    }),
    [onToggle]
  );

  const getDisclosureProps = useCallback(
    <T extends object>(
      props: T = {} as T
    ): T & { open: boolean; onClose: () => void } => ({
      ...props,
      open: isOpen,
      onClose: onClose,
    }),
    [isOpen, onClose]
  );

  return {
    isOpen,
    onOpen,
    onClose,
    onToggle,
    getButtonProps,
    getDisclosureProps,
  };
}

export default useDisclosure;
