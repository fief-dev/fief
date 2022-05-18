import * as R from 'ramda';

import * as schemas from '../schemas';

const isAllNilProperties: (o: any) => boolean = R.allPass([R.is(Object), R.pipe(R.values, R.all(R.isNil))]);
const rejectNilData = R.reject(R.anyPass([R.isNil, isAllNilProperties]));

export const cleanUserRequestData = <S extends schemas.user.UserCreateInternal | schemas.user.UserUpdate>(data: S): S => {
  return {
    ...rejectNilData(data),
    ...data.fields ? { fields: rejectNilData(data.fields) } : {},
  } as S;
};
