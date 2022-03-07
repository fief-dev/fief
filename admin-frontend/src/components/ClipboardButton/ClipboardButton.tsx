import useClipboard from 'react-use-clipboard';

interface ClipboardButtonProps {
  text: string;
}

const ClipboardButton: React.FunctionComponent<ClipboardButtonProps> = ({ text }) => {
  const [copied, setCopied] = useClipboard(text, { successDuration: 5000 });

  return (
    <button type="button" onClick={setCopied}>
      {!copied &&
        <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current" width="16" height="16" viewBox="0 0 24 24" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path stroke="none" d="M0 0h24v24H0z" fill="none" />
          <path d="M9 5h-2a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-12a2 2 0 0 0 -2 -2h-2" />
          <rect x="9" y="3" width="6" height="4" rx="2" />
        </svg>
      }
      {copied &&
        <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current" width="16" height="16" viewBox="0 0 24 24" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path stroke="none" d="M0 0h24v24H0z" fill="none" />
          <path d="M9 5h-2a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-12a2 2 0 0 0 -2 -2h-2" />
          <rect x="9" y="3" width="6" height="4" rx="2" />
          <path d="M9 14l2 2l4 -4" />
        </svg>
      }
    </button>
  );
};

export default ClipboardButton;
