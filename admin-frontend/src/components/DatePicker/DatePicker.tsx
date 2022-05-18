import { useDatePicker } from '../../hooks/datepicker';

interface DatePickerProps {
  value?: string | null;
  onChange?: (value: string | null) => void;
  time: boolean;
}

const DatePicker: React.FunctionComponent<DatePickerProps> = ({ value, onChange, time }) => {
  const dateElement = useDatePicker(value, time, onChange);
  return (
    <div>
      <input
        ref={dateElement}
        className="form-input w-full"
        type="text"
      />
    </div>
  );
};

export default DatePicker;
