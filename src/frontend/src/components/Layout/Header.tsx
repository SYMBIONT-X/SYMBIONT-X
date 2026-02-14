import {
  makeStyles,
  tokens,
  shorthands,
  Text,
  Avatar,
  Menu,
  MenuTrigger,
  MenuPopover,
  MenuList,
  MenuItem,
  Badge,
  Button,
  Tooltip,
} from '@fluentui/react-components';
import {
  AlertRegular,
  SettingsRegular,
  PersonRegular,
  SignOutRegular,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: '56px',
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottom: `1px solid ${tokens.colorNeutralStroke1}`,
    ...shorthands.padding('0', '24px'),
  },
  left: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('16px'),
  },
  right: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('12px'),
  },
  title: {
    fontWeight: tokens.fontWeightSemibold,
  },
  notificationButton: {
    position: 'relative',
  },
  badge: {
    position: 'absolute',
    top: '-4px',
    right: '-4px',
  },
});

export const Header: React.FC = () => {
  const styles = useStyles();

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <Text size={500} className={styles.title}>
          Security Dashboard
        </Text>
      </div>

      <div className={styles.right}>
        {/* Notifications */}
        <Tooltip content="Notifications" relationship="label">
          <div className={styles.notificationButton}>
            <Button
              appearance="subtle"
              icon={<AlertRegular />}
              aria-label="Notifications"
            />
            <Badge 
              className={styles.badge}
              size="small" 
              appearance="filled" 
              color="danger"
            >
              3
            </Badge>
          </div>
        </Tooltip>

        {/* Settings */}
        <Tooltip content="Settings" relationship="label">
          <Button
            appearance="subtle"
            icon={<SettingsRegular />}
            aria-label="Settings"
          />
        </Tooltip>

        {/* User Menu */}
        <Menu>
          <MenuTrigger disableButtonEnhancement>
            <Button appearance="subtle" aria-label="User menu">
              <Avatar
                name="Security Admin"
                size={32}
                color="brand"
              />
            </Button>
          </MenuTrigger>
          <MenuPopover>
            <MenuList>
              <MenuItem icon={<PersonRegular />}>Profile</MenuItem>
              <MenuItem icon={<SettingsRegular />}>Settings</MenuItem>
              <MenuItem icon={<SignOutRegular />}>Sign out</MenuItem>
            </MenuList>
          </MenuPopover>
        </Menu>
      </div>
    </header>
  );
};
