import { useFormattedDateTime } from '../../hooks/datetime';

interface DateTimeProps {
  datetime: string | Date;
  displayTime?: boolean;
}

const DateTime: React.FunctionComponent<React.PropsWithChildren<DateTimeProps>> = ({ datetime, displayTime }) => {
  const formatted = useFormattedDateTime(datetime, displayTime ? displayTime : false);
  return (
    <>{formatted}</>
  );
};

export default DateTime;
