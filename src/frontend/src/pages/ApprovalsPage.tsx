import { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Title1 as Title,
  Text,
  Button,
  Spinner,
  Badge,
  Textarea,
} from '@fluentui/react-components';
import {
  Checkmark24Regular,
  Dismiss24Regular,
  ArrowSync24Regular,
  Clock24Regular,
  Comment24Regular,
} from '@fluentui/react-icons';
import { hitlService } from '../services';
import type { Approval, Comment } from '../services/hitl.service';

const priorityColors: Record<string, 'danger' | 'warning' | 'informative' | 'success'> = {
  P0: 'danger',
  P1: 'danger',
  P2: 'warning',
  P3: 'informative',
  P4: 'success',
};

export function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedApproval, setSelectedApproval] = useState<Approval | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [decisionComment, setDecisionComment] = useState('');
  const [processing, setProcessing] = useState(false);

  const fetchApprovals = useCallback(async () => {
    try {
      const response = await hitlService.getPendingApprovals();
      setApprovals(response.approvals);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch approvals');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchApprovals();
    const interval = setInterval(fetchApprovals, 10000);
    return () => clearInterval(interval);
  }, [fetchApprovals]);

  const handleSelectApproval = async (approval: Approval) => {
    setSelectedApproval(approval);
    try {
      const response = await hitlService.getComments(approval.approval_id);
      setComments(response.comments);
    } catch {
      setComments([]);
    }
  };

  const handleDecision = async (approved: boolean) => {
    if (!selectedApproval) return;
    
    setProcessing(true);
    try {
      await hitlService.decideApproval(selectedApproval.approval_id, {
        approved,
        resolver: 'admin', // In real app, get from auth
        comment: decisionComment || undefined,
      });
      
      setSelectedApproval(null);
      setDecisionComment('');
      await fetchApprovals();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process decision');
    } finally {
      setProcessing(false);
    }
  };

  const handleAddComment = async () => {
    if (!selectedApproval || !newComment.trim()) return;
    
    try {
      await hitlService.addComment({
        target_type: 'approval',
        target_id: selectedApproval.approval_id,
        author: 'admin',
        content: newComment,
      });
      
      setNewComment('');
      const response = await hitlService.getComments(selectedApproval.approval_id);
      setComments(response.comments);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add comment');
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const timeUntilExpiry = (expiresAt: string | null) => {
    if (!expiresAt) return null;
    const diff = new Date(expiresAt).getTime() - Date.now();
    if (diff < 0) return 'Expired';
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m remaining`;
  };

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spinner size="large" label="Loading approvals..." />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <Title>Pending Approvals</Title>
          <Text style={{ color: '#64748b' }}>Review and approve remediation requests</Text>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Badge appearance="filled" color={approvals.length > 0 ? 'warning' : 'success'}>
            {approvals.length} pending
          </Badge>
          <Button icon={<ArrowSync24Regular />} onClick={fetchApprovals}>
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Card style={{ padding: '12px', marginBottom: '16px', backgroundColor: '#fef2f2' }}>
          <Text style={{ color: '#dc2626' }}>{error}</Text>
        </Card>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: selectedApproval ? '1fr 1fr' : '1fr', gap: '24px' }}>
        {/* Approvals List */}
        <div>
          {approvals.length === 0 ? (
            <Card style={{ padding: '32px', textAlign: 'center' }}>
              <Checkmark24Regular style={{ width: 48, height: 48, color: '#16a34a', marginBottom: '16px' }} />
              <Text size={500} weight="semibold" style={{ display: 'block' }}>
                All caught up!
              </Text>
              <Text style={{ color: '#64748b' }}>No pending approvals at this time.</Text>
            </Card>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {approvals.map((approval) => (
                <Card
                  key={approval.approval_id}
                  style={{
                    padding: '16px',
                    cursor: 'pointer',
                    border: selectedApproval?.approval_id === approval.approval_id
                      ? '2px solid #2563eb'
                      : '1px solid #e5e7eb',
                  }}
                  onClick={() => handleSelectApproval(approval)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px' }}>
                        <Badge appearance="filled" color={priorityColors[approval.priority] || 'informative'}>
                          {approval.priority}
                        </Badge>
                        <Badge appearance="outline" color="informative">
                          {approval.vulnerability_ids.length} vulnerabilities
                        </Badge>
                      </div>
                      <Text weight="semibold" style={{ display: 'block', marginBottom: '4px' }}>
                        {approval.title}
                      </Text>
                      <Text size={200} style={{ color: '#64748b' }}>
                        Workflow: {approval.workflow_id.slice(0, 8)}...
                      </Text>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      {approval.expires_at && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#ca8a04' }}>
                          <Clock24Regular style={{ width: 16, height: 16 }} />
                          <Text size={200}>{timeUntilExpiry(approval.expires_at)}</Text>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Approval Details */}
        {selectedApproval && (
          <Card style={{ padding: '20px' }}>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                <Badge appearance="filled" color={priorityColors[selectedApproval.priority] || 'informative'}>
                  {selectedApproval.priority}
                </Badge>
                <Badge appearance="outline">{selectedApproval.approval_type}</Badge>
              </div>
              <Text size={500} weight="semibold" style={{ display: 'block' }}>
                {selectedApproval.title}
              </Text>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <Text weight="medium" size={300}>Description</Text>
              <Text style={{ display: 'block', marginTop: '4px', color: '#374151' }}>
                {selectedApproval.description}
              </Text>
            </div>

            {selectedApproval.risk_summary && (
              <div style={{ marginBottom: '16px' }}>
                <Text weight="medium" size={300}>Risk Summary</Text>
                <Text style={{ display: 'block', marginTop: '4px', color: '#374151' }}>
                  {selectedApproval.risk_summary}
                </Text>
              </div>
            )}

            {selectedApproval.recommended_action && (
              <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#f0fdf4', borderRadius: '8px' }}>
                <Text weight="medium" size={300}>Recommended Action</Text>
                <Text style={{ display: 'block', marginTop: '4px' }}>
                  {selectedApproval.recommended_action}
                </Text>
              </div>
            )}

            <div style={{ marginBottom: '16px' }}>
              <Text weight="medium" size={300}>Details</Text>
              <div style={{ marginTop: '8px', fontSize: '14px', color: '#64748b' }}>
                <div>Requested by: {selectedApproval.requested_by}</div>
                <div>Requested at: {formatDate(selectedApproval.requested_at)}</div>
                <div>Vulnerabilities: {selectedApproval.vulnerability_ids.length}</div>
              </div>
            </div>

            {/* Comments Section */}
            <div style={{ marginBottom: '16px', borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Comment24Regular />
                <Text weight="medium">Comments ({comments.length})</Text>
              </div>
              
              {comments.map((comment) => (
                <div
                  key={comment.comment_id}
                  style={{ padding: '8px', backgroundColor: '#f8fafc', borderRadius: '4px', marginBottom: '8px' }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text weight="medium" size={200}>{comment.author}</Text>
                    <Text size={200} style={{ color: '#64748b' }}>
                      {formatDate(comment.created_at)}
                    </Text>
                  </div>
                  <Text size={300}>{comment.content}</Text>
                </div>
              ))}

              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <Textarea
                  placeholder="Add a comment..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  style={{ flex: 1 }}
                />
                <Button onClick={handleAddComment} disabled={!newComment.trim()}>
                  Add
                </Button>
              </div>
            </div>

            {/* Decision Section */}
            <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
              <Text weight="medium" size={300} style={{ marginBottom: '8px', display: 'block' }}>
                Decision Comment (optional)
              </Text>
              <Textarea
                placeholder="Add a comment about your decision..."
                value={decisionComment}
                onChange={(e) => setDecisionComment(e.target.value)}
                style={{ width: '100%', marginBottom: '12px' }}
              />
              
              <div style={{ display: 'flex', gap: '12px' }}>
                <Button
                  appearance="primary"
                  icon={<Checkmark24Regular />}
                  onClick={() => handleDecision(true)}
                  disabled={processing}
                  style={{ flex: 1 }}
                >
                  Approve
                </Button>
                <Button
                  appearance="secondary"
                  icon={<Dismiss24Regular />}
                  onClick={() => handleDecision(false)}
                  disabled={processing}
                  style={{ flex: 1 }}
                >
                  Reject
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
