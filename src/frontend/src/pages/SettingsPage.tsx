import {
  makeStyles,
  shorthands,
  Text,
  tokens,
  Card,
  CardHeader,
  Switch,
  Input,
  Button,
  Divider,
} from '@fluentui/react-components';
import { SaveRegular } from '@fluentui/react-icons';

const useStyles = makeStyles({
  page: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('24px'),
    maxWidth: '800px',
  },
  card: {
    ...shorthands.padding('24px'),
  },
  section: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('16px'),
  },
  settingRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    ...shorthands.padding('8px', '0'),
  },
  settingInfo: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('4px'),
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('8px'),
  },
  actions: {
    display: 'flex',
    justifyContent: 'flex-end',
    ...shorthands.gap('12px'),
    marginTop: '16px',
  },
});

export const SettingsPage: React.FC = () => {
  const styles = useStyles();

  return (
    <div className={styles.page}>
      {/* Header */}
      <div>
        <Text size={700} weight="semibold" block>
          Settings
        </Text>
        <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
          Configure SYMBIONT-X platform settings
        </Text>
      </div>

      {/* Auto-Remediation Settings */}
      <Card className={styles.card}>
        <CardHeader
          header={<Text weight="semibold" size={500}>Auto-Remediation</Text>}
          description="Configure automatic vulnerability remediation behavior"
        />
        <div className={styles.section}>
          <div className={styles.settingRow}>
            <div className={styles.settingInfo}>
              <Text weight="medium">Enable Auto-Remediation</Text>
              <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                Automatically create pull requests for detected vulnerabilities
              </Text>
            </div>
            <Switch defaultChecked />
          </div>

          <Divider />

          <div className={styles.settingRow}>
            <div className={styles.settingInfo}>
              <Text weight="medium">Auto-merge Low Risk Fixes</Text>
              <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                Automatically merge PRs for low-risk dependency updates
              </Text>
            </div>
            <Switch />
          </div>

          <Divider />

          <div className={styles.settingRow}>
            <div className={styles.settingInfo}>
              <Text weight="medium">Require Human Approval for Critical</Text>
              <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                Always require manual approval for critical severity fixes
              </Text>
            </div>
            <Switch defaultChecked />
          </div>
        </div>
      </Card>

      {/* Notification Settings */}
      <Card className={styles.card}>
        <CardHeader
          header={<Text weight="semibold" size={500}>Notifications</Text>}
          description="Configure alerting and notification preferences"
        />
        <div className={styles.section}>
          <div className={styles.settingRow}>
            <div className={styles.settingInfo}>
              <Text weight="medium">Email Notifications</Text>
              <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                Receive email alerts for critical vulnerabilities
              </Text>
            </div>
            <Switch defaultChecked />
          </div>

          <Divider />

          <div className={styles.settingRow}>
            <div className={styles.settingInfo}>
              <Text weight="medium">Slack Integration</Text>
              <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                Send alerts to Slack channels
              </Text>
            </div>
            <Switch />
          </div>
        </div>
      </Card>

      {/* API Configuration */}
      <Card className={styles.card}>
        <CardHeader
          header={<Text weight="semibold" size={500}>API Configuration</Text>}
          description="Configure external service integrations"
        />
        <div className={styles.section}>
          <div className={styles.inputGroup}>
            <Text weight="medium">GitHub Organization</Text>
            <Input placeholder="your-org" defaultValue="SYMBIONT-X" />
          </div>

          <div className={styles.inputGroup}>
            <Text weight="medium">Default Repository</Text>
            <Input placeholder="repository-name" defaultValue="SYMBIONT-X" />
          </div>

          <div className={styles.actions}>
            <Button appearance="secondary">Cancel</Button>
            <Button appearance="primary" icon={<SaveRegular />}>
              Save Changes
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};
