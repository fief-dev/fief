import { useFormattedDateTime } from '../../hooks/datetime';

interface DateTimeProps {
  datetime: string | Date;
  displayTime?: boolean;
}

const DateTime: React.FunctionComponent<DateTimeProps> = ({ datetime, displayTime }) => {
  const formatted = useFormattedDateTime(datetime, displayTime ? displayTime : false);
  return (
    <>{formatted}</>
  );
};

export default DateTime;
