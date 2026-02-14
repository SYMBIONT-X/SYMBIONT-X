import { useLocation, useNavigate } from 'react-router-dom';
import {
  makeStyles,
  tokens,
  shorthands,
  Text,
  Button,
  Tooltip,
} from '@fluentui/react-components';
import {
  HomeRegular,
  HomeFilled,
  ShieldErrorRegular,
  ShieldErrorFilled,
  BotRegular,
  BotFilled,
  SettingsRegular,
  SettingsFilled,
  ChevronLeftRegular,
  ChevronRightRegular,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    backgroundColor: tokens.colorNeutralBackground1,
    borderRight: `1px solid ${tokens.colorNeutralStroke1}`,
    transition: 'width 0.2s ease',
  },
  expanded: {
    width: '240px',
  },
  collapsed: {
    width: '60px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: '56px',
    ...shorthands.padding('0', '12px'),
    borderBottom: `1px solid ${tokens.colorNeutralStroke1}`,
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('12px'),
  },
  logoIcon: {
    width: '32px',
    height: '32px',
    backgroundColor: tokens.colorBrandBackground,
    ...shorthands.borderRadius('8px'),
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontWeight: tokens.fontWeightBold,
    fontSize: '16px',
  },
  nav: {
    flex: 1,
    ...shorthands.padding('12px', '8px'),
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('4px'),
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('12px'),
    ...shorthands.padding('10px', '12px'),
    ...shorthands.borderRadius('8px'),
    cursor: 'pointer',
    transition: 'background-color 0.15s ease',
    ':hover': {
      backgroundColor: tokens.colorNeutralBackground3,
    },
  },
  navItemActive: {
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1,
    ':hover': {
      backgroundColor: tokens.colorBrandBackground2,
    },
  },
  navIcon: {
    fontSize: '20px',
    flexShrink: 0,
  },
  footer: {
    ...shorthands.padding('12px', '8px'),
    borderTop: `1px solid ${tokens.colorNeutralStroke1}`,
  },
});

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactElement;
  iconActive: React.ReactElement;
}

const navItems: NavItem[] = [
  {
    path: '/dashboard',
    label: 'Dashboard',
    icon: <HomeRegular />,
    iconActive: <HomeFilled />,
  },
  {
    path: '/vulnerabilities',
    label: 'Vulnerabilities',
    icon: <ShieldErrorRegular />,
    iconActive: <ShieldErrorFilled />,
  },
  {
    path: '/agents',
    label: 'Agents',
    icon: <BotRegular />,
    iconActive: <BotFilled />,
  },
  {
    path: '/settings',
    label: 'Settings',
    icon: <SettingsRegular />,
    iconActive: <SettingsFilled />,
  },
];

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggle }) => {
  const styles = useStyles();
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <aside className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : styles.expanded}`}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.logo}>
          <div className={styles.logoIcon}>S</div>
          {!isCollapsed && (
            <Text weight="semibold" size={400}>
              SYMBIONT-X
            </Text>
          )}
        </div>
        {!isCollapsed && (
          <Button
            appearance="subtle"
            icon={<ChevronLeftRegular />}
            onClick={onToggle}
            size="small"
          />
        )}
      </div>

      {/* Navigation */}
      <nav className={styles.nav}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const navContent = (
            <div
              key={item.path}
              className={`${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
              onClick={() => navigate(item.path)}
              role="button"
              tabIndex={0}
            >
              <span className={styles.navIcon}>
                {isActive ? item.iconActive : item.icon}
              </span>
              {!isCollapsed && <Text>{item.label}</Text>}
            </div>
          );

          return isCollapsed ? (
            <Tooltip key={item.path} content={item.label} relationship="label" positioning="after">
              {navContent}
            </Tooltip>
          ) : (
            navContent
          );
        })}
      </nav>

      {/* Footer - Toggle button when collapsed */}
      {isCollapsed && (
        <div className={styles.footer}>
          <Button
            appearance="subtle"
            icon={<ChevronRightRegular />}
            onClick={onToggle}
            style={{ width: '100%' }}
          />
        </div>
      )}
    </aside>
  );
};
