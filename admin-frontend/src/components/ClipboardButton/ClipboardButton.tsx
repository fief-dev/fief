import useClipboard from 'react-use-clipboard';
import { ClipboardIcon, ClipboardCheckIcon } from '@heroicons/react/solid';

interface ClipboardButtonProps {
  text: string;
}

const ClipboardButton: React.FunctionComponent<React.PropsWithChildren<ClipboardButtonProps>> = ({ text }) => {
  const [copied, setCopied] = useClipboard(text, { successDuration: 5000 });

  return (
    <button type="button" onClick={setCopied}>
      <div className="pointer-events-none">
        {!copied &&
          <ClipboardIcon width={16} height={16} className="fill-current" />
        }
        {copied &&
          <ClipboardCheckIcon width={16} height={16} className="fill-current" />
        }
      </div>
    </button>
  );
};

export default ClipboardButton;
