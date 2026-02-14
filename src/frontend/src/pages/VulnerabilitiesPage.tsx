import {
  makeStyles,
  shorthands,
  Text,
  tokens,
  Card,
  Button,
  Input,
  Dropdown,
  Option,
} from '@fluentui/react-components';
import {
  SearchRegular,
  FilterRegular,
  ArrowDownloadRegular,
} from '@fluentui/react-icons';
import { VulnerabilityList } from '@components/Vulnerabilities/VulnerabilityList';

const useStyles = makeStyles({
  page: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('24px'),
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    flexWrap: 'wrap',
    ...shorthands.gap('16px'),
  },
  filters: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('12px'),
    flexWrap: 'wrap',
  },
  searchInput: {
    minWidth: '280px',
  },
  card: {
    ...shorthands.padding('0'),
  },
});

export const VulnerabilitiesPage: React.FC = () => {
  const styles = useStyles();

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <Text size={700} weight="semibold" block>
            Vulnerabilities
          </Text>
          <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
            Monitor, assess, and remediate security vulnerabilities
          </Text>
        </div>

        <div className={styles.filters}>
          <Input
            className={styles.searchInput}
            placeholder="Search CVE, package, or description..."
            contentBefore={<SearchRegular />}
          />
          
          <Dropdown placeholder="Severity" style={{ minWidth: '120px' }}>
            <Option value="all">All</Option>
            <Option value="critical">Critical</Option>
            <Option value="high">High</Option>
            <Option value="medium">Medium</Option>
            <Option value="low">Low</Option>
          </Dropdown>

          <Dropdown placeholder="Status" style={{ minWidth: '140px' }}>
            <Option value="all">All Status</Option>
            <Option value="open">Open</Option>
            <Option value="in_progress">In Progress</Option>
            <Option value="resolved">Resolved</Option>
          </Dropdown>

          <Button icon={<FilterRegular />} appearance="subtle">
            More Filters
          </Button>

          <Button icon={<ArrowDownloadRegular />} appearance="subtle">
            Export
          </Button>
        </div>
      </div>

      {/* Vulnerability List */}
      <Card className={styles.card}>
        <VulnerabilityList />
      </Card>
    </div>
  );
};
