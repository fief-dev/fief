import { CheckIcon, XIcon } from '@heroicons/react/solid';
import React, { useMemo } from 'react';

import { formatDateTime } from '../../hooks/datetime';
import * as schemas from '../../schemas';;

interface UserFieldValueProps {
  userField: schemas.userField.UserField;
  value: any;
}

const UserFieldValue: React.FunctionComponent<React.PropsWithChildren<UserFieldValueProps>> = ({ userField, value }) => {
  const { type, configuration: { choices } } = userField;

  const valueElement: React.ReactElement = useMemo(() => {
    if (value === undefined || value === null) {
      return <></>;
    }

    let valueElement: React.ReactElement;
    switch (type) {
      case schemas.userField.UserFieldType.BOOLEAN:
        valueElement = value ?
          <CheckIcon className="w-4 h-4 fill-current" /> :
          <XIcon className="w-4 h-4 fill-current" />
          ;
        break;
      case schemas.userField.UserFieldType.DATE:
        valueElement = <>{formatDateTime(value, false)}</>;
        break;
      case schemas.userField.UserFieldType.DATETIME:
        valueElement = <>{formatDateTime(value, true)}</>;
        break;
      case schemas.userField.UserFieldType.CHOICE:
        const choice = choices?.find((choice) => choice[0] === value);
        const choiceLabel = choice ? choice[1] : value;
        valueElement = <>{choiceLabel}</>;
        break;
      case schemas.userField.UserFieldType.ADDRESS:
        valueElement = (
          <>
            <span>{value.line1}</span>
            {value.line2 && <span> {value.line2}</span>}
            <span>, </span>
            <span>{value.postal_code} </span>
            <span>{value.city}, </span>
            {value.state && <span>{value.state}, </span>}
            <span>{value.country}</span>
          </>
        );
        break;
      default:
        valueElement = <>{value}</>;
    }
    return valueElement;
  }, [type, choices, value]);

  return valueElement;
};

export default UserFieldValue;
