import * as schemas from '../../schemas';

interface UserAvatarProps {
  user: schemas.user.CurrentUser;
}

const UserAvatar: React.FunctionComponent<React.PropsWithChildren<UserAvatarProps>> = ({ user }) => {
  return (
    <div className="w-8 h-8 rounded-full flex justify-center items-center bg-primary text-white">{user.email[0].toUpperCase()}</div>
  );
};

export default UserAvatar;
