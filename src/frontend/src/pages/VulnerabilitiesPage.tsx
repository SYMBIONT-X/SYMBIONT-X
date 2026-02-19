import { useState, useEffect } from 'react';
import {
  Card,
  Title1 as Title,
  Text,
  Spinner,
  Badge,
  
  Input,
  Dropdown,
  Option,
} from '@fluentui/react-components';
import { Search24Regular } from '@fluentui/react-icons';
import { useWorkflows } from '../hooks';
import type { RiskAssessment, Priority } from '../types/api.types';

const priorityColors: Record<Priority, 'danger' | 'warning' | 'informative' | 'success'> = {
  P0: 'danger',
  P1: 'danger',
  P2: 'warning',
  P3: 'informative',
  P4: 'success',
};

const severityColors: Record<string, 'danger' | 'warning' | 'informative' | 'success'> = {
  critical: 'danger',
  high: 'danger',
  medium: 'warning',
  low: 'informative',
  unknown: 'success',
};

export function VulnerabilitiesPage() {
  const { workflows, loading } = useWorkflows(5000);
  const [vulnerabilities, setVulnerabilities] = useState<RiskAssessment[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');

  useEffect(() => {
    // Extract vulnerabilities from completed workflows
    const allVulns: RiskAssessment[] = [];
    
    workflows.forEach((workflow) => {
      const assessStep = workflow.steps.find((s) => s.step_id === 'assess');
      if (assessStep?.output_data?.assessments) {
        const assessments = assessStep.output_data.assessments as RiskAssessment[];
        allVulns.push(...assessments);
      }
    });

    setVulnerabilities(allVulns);
  }, [workflows]);

  const filteredVulns = vulnerabilities.filter((vuln) => {
    const matchesSearch =
      vuln.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vuln.vulnerability_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (vuln.cve_id?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);

    const matchesPriority =
      priorityFilter === 'all' || vuln.risk_score.priority === priorityFilter;

    return matchesSearch && matchesPriority;
  });

  const summary = {
    P0: vulnerabilities.filter((v) => v.risk_score.priority === 'P0').length,
    P1: vulnerabilities.filter((v) => v.risk_score.priority === 'P1').length,
    P2: vulnerabilities.filter((v) => v.risk_score.priority === 'P2').length,
    P3: vulnerabilities.filter((v) => v.risk_score.priority === 'P3').length,
    P4: vulnerabilities.filter((v) => v.risk_score.priority === 'P4').length,
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title>Vulnerabilities</Title>
        <Text>View and manage detected security vulnerabilities</Text>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', marginBottom: '24px' }}>
        {Object.entries(summary).map(([priority, count]) => (
          <Card
            key={priority}
            style={{ padding: '16px', textAlign: 'center', cursor: 'pointer' }}
            onClick={() => setPriorityFilter(priority === priorityFilter ? 'all' : priority)}
          >
            <Badge appearance="filled" color={priorityColors[priority as Priority]}>
              {priority}
            </Badge>
            <Text size={600} weight="semibold" style={{ display: 'block', marginTop: '8px' }}>
              {count}
            </Text>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <Card style={{ padding: '16px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <Input
            placeholder="Search vulnerabilities..."
            contentBefore={<Search24Regular />}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flex: 1 }}
          />
          <Dropdown
            placeholder="Filter by priority"
            value={priorityFilter === 'all' ? 'All Priorities' : priorityFilter}
            onOptionSelect={(_, data) => setPriorityFilter(data.optionValue || 'all')}
          >
            <Option value="all">All Priorities</Option>
            <Option value="P0">P0 - Critical</Option>
            <Option value="P1">P1 - High</Option>
            <Option value="P2">P2 - Medium</Option>
            <Option value="P3">P3 - Low</Option>
            <Option value="P4">P4 - Info</Option>
          </Dropdown>
        </div>
      </Card>

      {/* Vulnerabilities List */}
      {loading ? (
        <Spinner size="large" label="Loading vulnerabilities..." />
      ) : filteredVulns.length === 0 ? (
        <Card style={{ padding: '32px', textAlign: 'center' }}>
          <Text style={{ color: '#666' }}>
            {vulnerabilities.length === 0
              ? 'No vulnerabilities found. Run a security scan to detect issues.'
              : 'No vulnerabilities match your filters.'}
          </Text>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {filteredVulns.map((vuln) => (
            <Card key={vuln.vulnerability_id} style={{ padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <Badge appearance="filled" color={priorityColors[vuln.risk_score.priority]}>
                      {vuln.risk_score.priority}
                    </Badge>
                    <Badge appearance="outline" color={severityColors[vuln.severity] || 'informative'}>
                      {vuln.severity}
                    </Badge>
                    {vuln.cve_id && (
                      <Badge appearance="outline" color="informative">
                        {vuln.cve_id}
                      </Badge>
                    )}
                  </div>
                  <Text weight="semibold" style={{ display: 'block', marginBottom: '4px' }}>
                    {vuln.title}
                  </Text>
                  <Text size={200} style={{ color: '#666' }}>
                    ID: {vuln.vulnerability_id}
                  </Text>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <Text size={300} weight="semibold">
                    Score: {vuln.risk_score.total_score.toFixed(1)}
                  </Text>
                  <Text size={200} style={{ color: '#666', display: 'block' }}>
                    {vuln.remediation_urgency}
                  </Text>
                </div>
              </div>
              <div style={{ marginTop: '12px', padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                <Text size={200}>{vuln.recommended_action}</Text>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
