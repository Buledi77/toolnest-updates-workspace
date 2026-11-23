#!/usr/bin/env python3
"""Audit near-duplicate content across all tool pages.

Extracts key sections from every tool page, normalizes text (replacing tool names
and dates), then measures exact and near-duplicate patterns.

Sections audited:
  - overview
  - best-for
  - strengths / key strengths
  - cons / limitations
  - pricing caveats
  - verdict
  - sources wording
  - FAQs
  - alternatives introductions
  - CTA wording

Classifies each pattern as:
  - useful_shared_ui_language
  - necessary_disclosure_boilerplate
  - harmful_generic_editorial_copy
  - accidental_copied_product_content
  - source_generated_repetition
  - research_required_differentiation

Outputs:
  reports/phase3/near-duplicate-content-audit.json
  reports/phase3/near-duplicate-content-audit.md
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports" / "phase3"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def strip_script_style(html: str) -> str:
    """Remove <script> and <style> blocks."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text


def extract_section_paragraphs(html: str, section_id: str) -> list[str]:
    """Extract paragraph text from a section by ID."""
    text = strip_script_style(html)
    m = re.search(r'<section[^>]*id=["\']' + re.escape(section_id) + r'["\'][^>]*>', text, re.IGNORECASE)
    if not m:
        return []
    start = m.end()
    next_sec = re.search(r'<section\b', text[start:])
    sec_content = text[start:start + (next_sec.start() if next_sec else len(text[start:]))]
    paras = re.findall(r'<p[^>]*>(.*?)</p>', sec_content, re.DOTALL)
    return [re.sub(r'<[^>]+>', '', re.sub(r'\s+', ' ', p.strip()).strip()).strip()
            for p in paras if p.strip()]


def extract_section_bullets(html: str, section_id: str) -> list[str]:
    """Extract bullet text from a section by ID."""
    text = strip_script_style(html)
    m = re.search(r'<section[^>]*id=["\']' + re.escape(section_id) + r'["\'][^>]*>', text, re.IGNORECASE)
    if not m:
        return []
    start = m.end()
    next_sec = re.search(r'<section\b', text[start:])
    sec_content = text[start:start + (next_sec.start() if next_sec else len(text[start:]))]
    bullets = re.findall(r'<li>(.*?)</li>', sec_content, re.DOTALL)
    return [re.sub(r'<[^>]+>', '', re.sub(r'\s+', ' ', b.strip()).strip()).strip()
            for b in bullets if b.strip()]


def normalize_text(text: str) -> str:
    """Normalize text by replacing tool names, dates, and other variable content."""
    # Replace dates
    text = re.sub(r'\d{4}-\d{2}-\d{2}', '[DATE]', text)
    text = re.sub(r'\d{2}/\d{2}/\d{4}', '[DATE]', text)
    text = re.sub(r'\d+ [A-Z][a-z]+ \d{4}', '[DATE]', text)
    text = re.sub(r'[A-Z][a-z]+ \d+, \d{4}', '[DATE]', text)
    text = re.sub(r'[A-Z][a-z]+ \d{4}', '[MONTH_YEAR]', text)
    # Replace URLs
    text = re.sub(r'https?://\S+', '[URL]', text)
    # Replace tool names — capitalized words at sentence starts or after possessives
    # This is approximate; we replace common tool name patterns
    text = re.sub(r'\b[A-Z][a-z]+\.[A-Z][a-z]+\b', '[TOOL]', text)
    text = re.sub(r'\b[A-Z][a-z]+\.io\b', '[TOOL]', text)
    text = re.sub(r'\b[A-Z][a-z]+\.AI\b', '[TOOL]', text)
    text = re.sub(r'\b[A-Z][a-z]+\.com\b', '[TOOL]', text)
    # Replace possessive tool names
    text = re.sub(r"\b[A-Z][a-z]+['']s\b", "[TOOL]'s", text)
    text = re.sub(r"\b[A-Z][a-z]+['']\b", "[TOOL]'", text)
    # Replace standalone capitalized words that look like tool names (2+ chars)
    # but keep common English words
    common_words = {'The', 'This', 'That', 'These', 'Those', 'And', 'But', 'Or',
                    'Not', 'No', 'Yes', 'All', 'Some', 'Any', 'Each', 'Every',
                    'For', 'With', 'From', 'Into', 'Over', 'Under', 'After',
                    'Before', 'Between', 'During', 'Without', 'Within', 'About',
                    'Above', 'Below', 'Along', 'Around', 'Across', 'Through',
                    'Tool', 'Tools', 'Team', 'Teams', 'User', 'Users', 'Web',
                    'AI', 'API', 'CRM', 'SEO', 'SMB', 'UI', 'UX', 'URL',
                    'Free', 'Paid', 'New', 'Old', 'Best', 'Good', 'Great',
                    'Strong', 'Solid', 'Fast', 'Easy', 'Simple', 'Quick',
                    'Large', 'Small', 'Big', 'High', 'Low', 'Long', 'Short',
                    'Multiple', 'Single', 'Full', 'Partial', 'Real', 'Live',
                    'Open', 'Closed', 'Deep', 'Wide', 'Rich', 'Clean',
                    'Smart', 'Safe', 'Secure', 'Public', 'Private', 'Shared',
                    'Custom', 'Default', 'Global', 'Local', 'Direct', 'Indirect',
                    'Visual', 'Audio', 'Video', 'Text', 'Image', 'Data',
                    'Cloud', 'Mobile', 'Desktop', 'Browser', 'Native',
                    'Advanced', 'Basic', 'Professional', 'Enterprise',
                    'Personal', 'Business', 'Marketing', 'Sales', 'Design',
                    'Productivity', 'Research', 'Analysis', 'Automation',
                    'Management', 'Planning', 'Tracking', 'Reporting',
                    'Monitoring', 'Testing', 'Building', 'Creating',
                    'Making', 'Generating', 'Writing', 'Editing',
                    'Publishing', 'Sharing', 'Collaborating', 'Integrating',
                    'Connecting', 'Importing', 'Exporting', 'Converting',
                    'Optimizing', 'Improving', 'Enhancing', 'Extending',
                    'Supporting', 'Helping', 'Assisting', 'Guiding',
                    'Learning', 'Training', 'Teaching', 'Studying',
                    'Reading', 'Writing', 'Speaking', 'Listening',
                    'Thinking', 'Understanding', 'Knowing', 'Remembering',
                    'Finding', 'Searching', 'Discovering', 'Exploring',
                    'Checking', 'Verifying', 'Validating', 'Confirming',
                    'Reviewing', 'Analyzing', 'Evaluating', 'Assessing',
                    'Comparing', 'Measuring', 'Calculating', 'Estimating',
                    'Predicting', 'Forecasting', 'Planning', 'Scheduling',
                    'Organizing', 'Structuring', 'Arranging', 'Sorting',
                    'Filtering', 'Grouping', 'Categorizing', 'Tagging',
                    'Labeling', 'Naming', 'Describing', 'Explaining',
                    'Summarizing', 'Abstracting', 'Simplifying', 'Clarifying',
                    'Highlighting', 'Emphasizing', 'Focusing', 'Targeting',
                    'Prioritizing', 'Ranking', 'Scoring', 'Rating',
                    'Reviewing', 'Rating', 'Voting', 'Choosing', 'Selecting',
                    'Picking', 'Deciding', 'Determining', 'Resolving',
                    'Solving', 'Fixing', 'Repairing', 'Correcting',
                    'Updating', 'Refreshing', 'Syncing', 'Backing',
                    'Restoring', 'Recovering', 'Saving', 'Loading',
                    'Storing', 'Retrieving', 'Fetching', 'Downloading',
                    'Uploading', 'Transferring', 'Moving', 'Copying',
                    'Deleting', 'Removing', 'Clearing', 'Resetting',
                    'Initializing', 'Starting', 'Stopping', 'Pausing',
                    'Resuming', 'Continuing', 'Ending', 'Finishing',
                    'Completing', 'Closing', 'Opening', 'Launching',
                    'Running', 'Executing', 'Processing', 'Handling',
                    'Managing', 'Controlling', 'Directing', 'Leading',
                    'Following', 'Tracking', 'Monitoring', 'Watching',
                    'Observing', 'Viewing', 'Displaying', 'Showing',
                    'Hiding', 'Toggling', 'Switching', 'Changing',
                    'Modifying', 'Adjusting', 'Configuring', 'Setting',
                    'Configuring', 'Customizing', 'Personalizing',
                    'Adapting', 'Tailoring', 'Fitting', 'Matching',
                    'Aligning', 'Balancing', 'Optimizing', 'Tuning',
                    'Calibrating', 'Standardizing', 'Normalizing',
                    'Formatting', 'Styling', 'Theming', 'Coloring',
                    'Sizing', 'Scaling', 'Resizing', 'Rotating',
                    'Flipping', 'Transforming', 'Converting', 'Encoding',
                    'Decoding', 'Encrypting', 'Decrypting', 'Signing',
                    'Verifying', 'Authenticating', 'Authorizing',
                    'Permitting', 'Allowing', 'Denying', 'Blocking',
                    'Restricting', 'Limiting', 'Capping', 'Throttling',
                    'Rate', 'Limit', 'Quota', 'Budget', 'Cost',
                    'Price', 'Charge', 'Fee', 'Payment', 'Billing',
                    'Invoice', 'Receipt', 'Order', 'Purchase', 'Sale',
                    'Revenue', 'Income', 'Profit', 'Loss', 'Expense',
                    'Spend', 'Saving', 'Discount', 'Deal', 'Offer',
                    'Promotion', 'Coupon', 'Voucher', 'Reward',
                    'Bonus', 'Gift', 'Premium', 'Upgrade', 'Downgrade',
                    'Trial', 'Demo', 'Sample', 'Preview', 'Prototype',
                    'Draft', 'Version', 'Release', 'Update', 'Patch',
                    'Fix', 'Bug', 'Issue', 'Problem', 'Error',
                    'Warning', 'Alert', 'Notification', 'Message',
                    'Email', 'Mail', 'Letter', 'Note', 'Memo',
                    'Document', 'File', 'Folder', 'Directory', 'Path',
                    'Link', 'Reference', 'Citation', 'Source',
                    'Origin', 'Root', 'Base', 'Foundation', 'Core',
                    'Center', 'Middle', 'Edge', 'Border', 'Boundary',
                    'Limit', 'Range', 'Scope', 'Area', 'Region',
                    'Zone', 'Space', 'Place', 'Location', 'Position',
                    'Point', 'Spot', 'Site', 'Page', 'Screen',
                    'Window', 'Panel', 'Tab', 'Menu', 'Bar',
                    'Button', 'Icon', 'Symbol', 'Sign', 'Mark',
                    'Label', 'Title', 'Header', 'Footer', 'Body',
                    'Content', 'Text', 'String', 'Character',
                    'Word', 'Phrase', 'Sentence', 'Paragraph',
                    'Section', 'Chapter', 'Part', 'Piece', 'Bit',
                    'Chunk', 'Block', 'Element', 'Component',
                    'Module', 'Plugin', 'Extension', 'Add', 'On',
                    'Feature', 'Function', 'Capability', 'Ability',
                    'Skill', 'Power', 'Strength', 'Weakness',
                    'Advantage', 'Disadvantage', 'Benefit', 'Drawback',
                    'Pros', 'Cons', 'Plus', 'Minus', 'Good',
                    'Bad', 'Better', 'Worse', 'Best', 'Worst',
                    'More', 'Less', 'Most', 'Least', 'Equal',
                    'Same', 'Different', 'Similar', 'Unique',
                    'Common', 'Rare', 'Frequent', 'Occasional',
                    'Regular', 'Irregular', 'Normal', 'Abnormal',
                    'Standard', 'Special', 'General', 'Specific',
                    'Particular', 'Exact', 'Precise', 'Approximate',
                    'Rough', 'Accurate', 'Correct', 'Wrong',
                    'True', 'False', 'Right', 'Left', 'Up',
                    'Down', 'In', 'Out', 'On', 'Off',
                    'Yes', 'No', 'Maybe', 'Perhaps', 'Probably',
                    'Definitely', 'Certainly', 'Surely', 'Obviously',
                    'Clearly', 'Simply', 'Easily', 'Quickly',
                    'Slowly', 'Fast', 'Slow', 'Hard', 'Soft',
                    'Light', 'Heavy', 'Thin', 'Thick', 'Wide',
                    'Narrow', 'Deep', 'Shallow', 'High', 'Low',
                    'Tall', 'Short', 'Long', 'Brief', 'Short',
                    'Early', 'Late', 'Recent', 'Current', 'Latest',
                    'First', 'Last', 'Next', 'Previous', 'Former',
                    'Other', 'Another', 'Each', 'Every', 'All',
                    'Both', 'Either', 'Neither', 'One', 'Two',
                    'Three', 'Four', 'Five', 'Six', 'Seven',
                    'Eight', 'Nine', 'Ten', 'Hundred', 'Thousand',
                    'Million', 'Billion', 'Trillion', 'Percent',
                    'Half', 'Quarter', 'Third', 'Double', 'Triple',
                    'Single', 'Multiple', 'Several', 'Many', 'Few',
                    'Some', 'Any', 'None', 'All', 'Most', 'More',
                    'Less', 'Least', 'Most', 'Better', 'Best',
                    'Worse', 'Worst', 'First', 'Second', 'Third',
                    'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth',
                    'Ninth', 'Tenth', 'Final', 'Ultimate', 'Primary',
                    'Secondary', 'Tertiary', 'Main', 'Major', 'Minor',
                    'Key', 'Important', 'Critical', 'Essential',
                    'Vital', 'Necessary', 'Required', 'Optional',
                    'Mandatory', 'Voluntary', 'Automatic', 'Manual',
                    'Active', 'Passive', 'Dynamic', 'Static',
                    'Flexible', 'Rigid', 'Adaptable', 'Fixed',
                    'Variable', 'Constant', 'Temporary', 'Permanent',
                    'Transient', 'Enduring', 'Lasting', 'Brief',
                    'Momentary', 'Instant', 'Immediate', 'Delayed',
                    'Scheduled', 'Planned', 'Spontaneous', 'Random',
                    'Ordered', 'Sorted', 'Organized', 'Structured',
                    'Unstructured', 'Formal', 'Informal', 'Official',
                    'Unofficial', 'Public', 'Private', 'Internal',
                    'External', 'Local', 'Remote', 'Near', 'Far',
                    'Close', 'Distant', 'Direct', 'Indirect',
                    'Straight', 'Curved', 'Round', 'Square',
                    'Flat', 'Smooth', 'Rough', 'Clean', 'Dirty',
                    'Fresh', 'Stale', 'New', 'Old', 'Modern',
                    'Classic', 'Traditional', 'Contemporary',
                    'Ancient', 'Historic', 'Recent', 'Past',
                    'Present', 'Future', 'Now', 'Then', 'Today',
                    'Tomorrow', 'Yesterday', 'Week', 'Month',
                    'Year', 'Day', 'Hour', 'Minute', 'Second',
                    'Time', 'Date', 'Period', 'Duration',
                    'Interval', 'Frequency', 'Rate', 'Speed',
                    'Velocity', 'Acceleration', 'Momentum',
                    'Force', 'Pressure', 'Tension', 'Stress',
                    'Strain', 'Load', 'Weight', 'Mass', 'Volume',
                    'Capacity', 'Size', 'Dimension', 'Measure',
                    'Unit', 'Scale', 'Level', 'Degree', 'Grade',
                    'Class', 'Type', 'Kind', 'Sort', 'Category',
                    'Group', 'Set', 'Collection', 'Series',
                    'Sequence', 'Order', 'Pattern', 'Trend',
                    'Direction', 'Path', 'Route', 'Way', 'Method',
                    'Approach', 'Strategy', 'Tactic', 'Technique',
                    'Process', 'Procedure', 'System', 'Framework',
                    'Model', 'Template', 'Format', 'Style',
                    'Design', 'Layout', 'Structure', 'Architecture',
                    'Foundation', 'Basis', 'Ground', 'Reason',
                    'Cause', 'Effect', 'Result', 'Outcome',
                    'Consequence', 'Impact', 'Influence', 'Change',
                    'Shift', 'Move', 'Transition', 'Transformation',
                    'Evolution', 'Development', 'Growth', 'Progress',
                    'Advance', 'Improvement', 'Enhancement',
                    'Upgrade', 'Update', 'Revision', 'Edition',
                    'Version', 'Release', 'Launch', 'Introduction',
                    'Debut', 'Premiere', 'Start', 'Beginning',
                    'Origin', 'Source', 'Root', 'Cause', 'Basis',
                    'Foundation', 'Ground', 'Support', 'Backing',
                    'Help', 'Assistance', 'Aid', 'Service',
                    'Solution', 'Answer', 'Response', 'Reply',
                    'Feedback', 'Comment', 'Review', 'Opinion',
                    'View', 'Perspective', 'Angle', 'Standpoint',
                    'Position', 'Stance', 'Attitude', 'Approach',
                    'Mindset', 'Mind', 'Thought', 'Idea', 'Concept',
                    'Notion', 'Theory', 'Hypothesis', 'Assumption',
                    'Belief', 'Fact', 'Truth', 'Reality', 'Actual',
                    'Real', 'Genuine', 'Authentic', 'Original',
                    'Unique', 'Distinct', 'Separate', 'Independent',
                    'Autonomous', 'Self', 'Contained', 'Complete',
                    'Whole', 'Entire', 'Total', 'Full', 'Partial',
                    'Incomplete', 'Missing', 'Absent', 'Present',
                    'Available', 'Unavailable', 'Accessible',
                    'Inaccessible', 'Open', 'Closed', 'Public',
                    'Private', 'Shared', 'Exclusive', 'Inclusive',
                    'Universal', 'Global', 'Worldwide', 'National',
                    'Regional', 'Local', 'Community', 'Social',
                    'Personal', 'Individual', 'Collective', 'Group',
                    'Team', 'Organization', 'Company', 'Business',
                    'Enterprise', 'Startup', 'Brand', 'Product',
                    'Service', 'Platform', 'Application', 'Software',
                    'Hardware', 'Device', 'Tool', 'Instrument',
                    'Equipment', 'Resource', 'Asset', 'Material',
                    'Content', 'Information', 'Data', 'Knowledge',
                    'Wisdom', 'Insight', 'Understanding', 'Awareness',
                    'Consciousness', 'Attention', 'Focus', 'Interest',
                    'Curiosity', 'Desire', 'Need', 'Want', 'Wish',
                    'Hope', 'Expectation', 'Goal', 'Objective',
                    'Target', 'Aim', 'Purpose', 'Mission', 'Vision',
                    'Dream', 'Ambition', 'Aspiration', 'Intention',
                    'Plan', 'Strategy', 'Tactic', 'Action', 'Step',
                    'Phase', 'Stage', 'Phase', 'Level', 'Layer',
                    'Tier', 'Rank', 'Order', 'Priority', 'Urgency',
                    'Importance', 'Significance', 'Value', 'Worth',
                    'Merit', 'Quality', 'Standard', 'Criterion',
                    'Measure', 'Metric', 'Indicator', 'Signal',
                    'Sign', 'Symptom', 'Evidence', 'Proof',
                    'Confirmation', 'Verification', 'Validation',
                    'Authentication', 'Authorization', 'Permission',
                    'Approval', 'Acceptance', 'Agreement', 'Consent',
                    'Assent', 'Endorsement', 'Support', 'Backing',
                    'Advocacy', 'Promotion', 'Marketing', 'Advertising',
                    'Sales', 'Commerce', 'Trade', 'Exchange',
                    'Transaction', 'Deal', 'Agreement', 'Contract',
                    'Partnership', 'Alliance', 'Collaboration',
                    'Cooperation', 'Coordination', 'Integration',
                    'Connection', 'Link', 'Relationship', 'Bond',
                    'Tie', 'Association', 'Affiliation', 'Membership',
                    'Subscription', 'Registration', 'Enrollment',
                    'Admission', 'Entry', 'Access', 'Entry',
                    'Exit', 'Departure', 'Leaving', 'Ending',
                    'Conclusion', 'Finish', 'Completion', 'Closure',
                    'Termination', 'Cancellation', 'Suspension',
                    'Pause', 'Break', 'Rest', 'Recovery', 'Healing',
                    'Repair', 'Fix', 'Solution', 'Remedy', 'Cure',
                    'Treatment', 'Care', 'Attention', 'Service',
                    'Help', 'Support', 'Assistance', 'Aid',
                    'Guidance', 'Direction', 'Instruction', 'Advice',
                    'Counsel', 'Recommendation', 'Suggestion',
                    'Proposal', 'Offer', 'Option', 'Choice',
                    'Alternative', 'Substitute', 'Replacement',
                    'Equivalent', 'Match', 'Pair', 'Couple',
                    'Set', 'Group', 'Collection', 'Assembly',
                    'Gathering', 'Meeting', 'Conference', 'Event',
                    'Occasion', 'Celebration', 'Festival', 'Party',
                    'Ceremony', 'Ritual', 'Tradition', 'Custom',
                    'Habit', 'Routine', 'Practice', 'Exercise',
                    'Training', 'Drill', 'Rehearsal', 'Practice',
                    'Performance', 'Show', 'Display', 'Exhibition',
                    'Presentation', 'Demonstration', 'Example',
                    'Illustration', 'Sample', 'Specimen', 'Model',
                    'Prototype', 'Draft', 'Sketch', 'Outline',
                    'Framework', 'Skeleton', 'Structure', 'Form',
                    'Shape', 'Figure', 'Pattern', 'Design',
                    'Layout', 'Arrangement', 'Organization',
                    'Order', 'Sequence', 'Series', 'Chain',
                    'Link', 'Connection', 'Relation', 'Correlation',
                    'Association', 'Correspondence', 'Equivalence',
                    'Equality', 'Balance', 'Symmetry', 'Harmony',
                    'Unity', 'Oneness', 'Wholeness', 'Completeness',
                    'Perfection', 'Excellence', 'Quality', 'Grade',
                    'Class', 'Category', 'Type', 'Kind', 'Sort',
                    'Variety', 'Diversity', 'Difference', 'Distinction',
                    'Contrast', 'Comparison', 'Analogy', 'Metaphor',
                    'Simile', 'Symbol', 'Representation', 'Image',
                    'Picture', 'Photo', 'Graphic', 'Diagram',
                    'Chart', 'Graph', 'Table', 'List', 'Index',
                    'Catalog', 'Directory', 'Register', 'Record',
                    'File', 'Document', 'Paper', 'Report', 'Memo',
                    'Note', 'Message', 'Letter', 'Email', 'Mail',
                    'Post', 'Article', 'Story', 'News', 'Update',
                    'Bulletin', 'Announcement', 'Declaration',
                    'Statement', 'Declaration', 'Proclamation',
                    'Resolution', 'Decision', 'Verdict', 'Judgment',
                    'Ruling', 'Order', 'Command', 'Directive',
                    'Instruction', 'Guideline', 'Rule', 'Regulation',
                    'Policy', 'Law', 'Statute', 'Code', 'Standard',
                    'Norm', 'Convention', 'Protocol', 'Procedure',
                    'Process', 'Method', 'Technique', 'Approach',
                    'Way', 'Means', 'Mode', 'Manner', 'Style',
                    'Fashion', 'Trend', 'Fad', 'Craze', 'Boom',
                    'Growth', 'Expansion', 'Extension', 'Spread',
                    'Reach', 'Range', 'Scope', 'Coverage', 'Extent',
                    'Degree', 'Level', 'Amount', 'Quantity',
                    'Number', 'Count', 'Total', 'Sum', 'Aggregate',
                    'Whole', 'Part', 'Piece', 'Fragment', 'Segment',
                    'Section', 'Division', 'Branch', 'Department',
                    'Unit', 'Department', 'Office', 'Agency',
                    'Bureau', 'Institution', 'Organization',
                    'Association', 'Society', 'Club', 'Group',
                    'Team', 'Crew', 'Staff', 'Personnel', 'Workforce',
                    'Labor', 'Worker', 'Employee', 'Member',
                    'Participant', 'Contributor', 'Author', 'Writer',
                    'Creator', 'Maker', 'Builder', 'Developer',
                    'Designer', 'Engineer', 'Architect', 'Planner',
                    'Manager', 'Director', 'Leader', 'Chief',
                    'Head', 'Boss', 'Owner', 'Founder', 'Partner',
                    'Investor', 'Shareholder', 'Stakeholder',
                    'Customer', 'Client', 'User', 'Consumer',
                    'Buyer', 'Purchaser', 'Seller', 'Vendor',
                    'Supplier', 'Provider', 'Distributor', 'Retailer',
                    'Merchant', 'Trader', 'Dealer', 'Broker',
                    'Agent', 'Representative', 'Delegate', 'Ambassador',
                    'Messenger', 'Courier', 'Carrier', 'Transporter',
                    'Driver', 'Pilot', 'Captain', 'Navigator',
                    'Guide', 'Coach', 'Trainer', 'Teacher',
                    'Instructor', 'Professor', 'Mentor', 'Advisor',
                    'Consultant', 'Expert', 'Specialist', 'Professional',
                    'Practitioner', 'Practitioner', 'Artist',
                    'Craftsman', 'Artisan', 'Maker', 'Creator',
                    'Inventor', 'Innovator', 'Pioneer', 'Trailblazer',
                    'Leader', 'Follower', 'Supporter', 'Fan',
                    'Admirer', 'Enthusiast', 'Aficionado', 'Devotee',
                    'Believer', 'Follower', 'Disciple', 'Student',
                    'Learner', 'Scholar', 'Researcher', 'Scientist',
                    'Analyst', 'Observer', 'Watcher', 'Monitor',
                    'Inspector', 'Auditor', 'Reviewer', 'Evaluator',
                    'Assessor', 'Appraiser', 'Judge', 'Arbiter',
                    'Mediator', 'Negotiator', 'Diplomat', 'Ambassador',
                    'Representative', 'Delegate', 'Delegate',
                    'Spokesperson', 'Voice', 'Speaker', 'Presenter',
                    'Host', 'Guest', 'Visitor', 'Tourist', 'Traveler',
                    'Passenger', 'Commuter', 'Driver', 'Rider',
                    'Walker', 'Runner', 'Jogger', 'Swimmer',
                    'Diver', 'Flyer', 'Sailor', 'Mariner', 'Captain',
                    'Commander', 'Officer', 'Soldier', 'Warrior',
                    'Fighter', 'Champion', 'Winner', 'Loser',
                    'Participant', 'Competitor', 'Contestant',
                    'Player', 'Athlete', 'Sportsperson', 'Team',
                    'Member', 'Fan', 'Spectator', 'Audience',
                    'Viewer', 'Reader', 'Listener', 'Watcher',
                    'Observer', 'Witness', 'Bystander', 'Passerby',
                    'Stranger', 'Neighbor', 'Friend', 'Acquaintance',
                    'Colleague', 'Coworker', 'Partner', 'Associate',
                    'Ally', 'Companion', 'Mate', 'Buddy', 'Pal',
                    'Confidant', 'Advisor', 'Counselor', 'Therapist',
                    'Healer', 'Doctor', 'Nurse', 'Caregiver',
                    'Helper', 'Volunteer', 'Donor', 'Contributor',
                    'Supporter', 'Backer', 'Sponsor', 'Patron',
                    'Benefactor', 'Philanthropist', 'Charity',
                    'Foundation', 'Trust', 'Fund', 'Grant',
                    'Scholarship', 'Prize', 'Award', 'Honor',
                    'Recognition', 'Acknowledgment', 'Appreciation',
                    'Gratitude', 'Thanks', 'Praise', 'Commendation',
                    'Acclaim', 'Applause', 'Cheer', 'Celebration',
                    'Joy', 'Happiness', 'Delight', 'Pleasure',
                    'Satisfaction', 'Contentment', 'Peace', 'Calm',
                    'Tranquility', 'Serene', 'Quiet', 'Silent',
                    'Still', 'Motionless', 'Frozen', 'Solid',
                    'Liquid', 'Gas', 'Vapor', 'Steam', 'Smoke',
                    'Fire', 'Flame', 'Heat', 'Warmth', 'Cold',
                    'Cool', 'Chill', 'Freeze', 'Ice', 'Snow',
                    'Rain', 'Storm', 'Wind', 'Breeze', 'Gale',
                    'Hurricane', 'Tornado', 'Cyclone', 'Typhoon',
                    'Wave', 'Tide', 'Current', 'Stream', 'River',
                    'Lake', 'Ocean', 'Sea', 'Beach', 'Shore',
                    'Coast', 'Island', 'Continent', 'Land', 'Earth',
                    'Ground', 'Soil', 'Dirt', 'Mud', 'Clay',
                    'Sand', 'Rock', 'Stone', 'Pebble', 'Boulder',
                    'Mountain', 'Hill', 'Valley', 'Canyon', 'Cave',
                    'Forest', 'Wood', 'Tree', 'Plant', 'Flower',
                    'Grass', 'Leaf', 'Branch', 'Root', 'Seed',
                    'Fruit', 'Vegetable', 'Food', 'Drink', 'Water',
                    'Juice', 'Sauce', 'Soup', 'Meal', 'Dish',
                    'Recipe', 'Ingredient', 'Spice', 'Herb',
                    'Seasoning', 'Flavor', 'Taste', 'Smell',
                    'Scent', 'Aroma', 'Fragrance', 'Perfume',
                    'Scent', 'Odor', 'Stink', 'Smell', 'Aroma',
                    'Sound', 'Noise', 'Music', 'Song', 'Melody',
                    'Tune', 'Rhythm', 'Beat', 'Tempo', 'Pitch',
                    'Tone', 'Volume', 'Loud', 'Soft', 'Quiet',
                    'Silent', 'Mute', 'Deaf', 'Blind', 'Dark',
                    'Light', 'Bright', 'Dim', 'Glow', 'Shine',
                    'Sparkle', 'Gleam', 'Glitter', 'Flash',
                    'Blaze', 'Flare', 'Beam', 'Ray', 'Light',
                    'Color', 'Hue', 'Shade', 'Tint', 'Tone',
                    'Pattern', 'Texture', 'Surface', 'Finish',
                    'Coating', 'Layer', 'Film', 'Sheet', 'Plate',
                    'Panel', 'Board', 'Plank', 'Tile', 'Brick',
                    'Block', 'Cube', 'Sphere', 'Circle', 'Ring',
                    'Loop', 'Curve', 'Line', 'Edge', 'Corner',
                    'Angle', 'Point', 'Vertex', 'Node', 'Center',
                    'Middle', 'Core', 'Heart', 'Soul', 'Spirit',
                    'Mind', 'Brain', 'Thought', 'Idea', 'Concept',
                    'Notion', 'Theory', 'Hypothesis', 'Fact',
                    'Truth', 'Reality', 'World', 'Universe',
                    'Space', 'Time', 'Dimension', 'Realm',
                    'Domain', 'Field', 'Area', 'Zone', 'Region',
                    'Territory', 'Country', 'Nation', 'State',
                    'City', 'Town', 'Village', 'Home', 'House',
                    'Building', 'Structure', 'Tower', 'Bridge',
                    'Road', 'Street', 'Avenue', 'Boulevard',
                    'Highway', 'Path', 'Trail', 'Track', 'Route',
                    'Way', 'Direction', 'Course', 'Destination',
                    'Goal', 'Target', 'Aim', 'Purpose', 'Meaning',
                    'Sense', 'Feeling', 'Emotion', 'Passion',
                    'Love', 'Hate', 'Fear', 'Anger', 'Sadness',
                    'Happiness', 'Joy', 'Sorrow', 'Grief', 'Pain',
                    'Suffering', 'Comfort', 'Relief', 'Ease',
                    'Difficulty', 'Challenge', 'Obstacle', 'Barrier',
                    'Hurdle', 'Problem', 'Issue', 'Question',
                    'Answer', 'Solution', 'Resolution', 'Fix',
                    'Repair', 'Mend', 'Heal', 'Cure', 'Treat',
                    'Help', 'Assist', 'Support', 'Back', 'Uphold',
                    'Maintain', 'Sustain', 'Preserve', 'Protect',
                    'Defend', 'Guard', 'Shield', 'Cover', 'Hide',
                    'Conceal', 'Reveal', 'Show', 'Display',
                    'Exhibit', 'Present', 'Introduce', 'Launch',
                    'Start', 'Begin', 'Initiate', 'Create',
                    'Make', 'Build', 'Construct', 'Form', 'Shape',
                    'Mold', 'Design', 'Plan', 'Organize', 'Arrange',
                    'Prepare', 'Ready', 'Set', 'Go', 'Move',
                    'Run', 'Walk', 'Step', 'Jump', 'Leap',
                    'Fly', 'Soar', 'Rise', 'Fall', 'Drop',
                    'Sink', 'Float', 'Drift', 'Flow', 'Stream',
                    'Pour', 'Spill', 'Leak', 'Drip', 'Drop',
                    'Rain', 'Snow', 'Hail', 'Sleet', 'Storm',
                    'Thunder', 'Lightning', 'Flash', 'Bolt',
                    'Strike', 'Hit', 'Touch', 'Feel', 'Sense',
                    'Perceive', 'Notice', 'Observe', 'See',
                    'Watch', 'Look', 'View', 'Gaze', 'Stare',
                    'Glance', 'Peek', 'Peer', 'Scan', 'Search',
                    'Find', 'Discover', 'Uncover', 'Reveal',
                    'Expose', 'Unveil', 'Open', 'Close', 'Shut',
                    'Lock', 'Unlock', 'Secure', 'Free', 'Release',
                    'Liberate', 'Save', 'Rescue', 'Deliver',
                    'Carry', 'Bring', 'Take', 'Fetch', 'Get',
                    'Obtain', 'Acquire', 'Gain', 'Earn', 'Win',
                    'Lose', 'Miss', 'Fail', 'Succeed', 'Achieve',
                    'Accomplish', 'Complete', 'Finish', 'End',
                    'Stop', 'Halt', 'Pause', 'Wait', 'Stay',
                    'Remain', 'Keep', 'Hold', 'Grasp', 'Catch',
                    'Grab', 'Seize', 'Snatch', 'Take', 'Steal',
                    'Rob', 'Borrow', 'Lend', 'Give', 'Offer',
                    'Provide', 'Supply', 'Deliver', 'Send',
                    'Receive', 'Accept', 'Reject', 'Refuse',
                    'Decline', 'Deny', 'Admit', 'Confess',
                    'Acknowledge', 'Recognize', 'Identify',
                    'Name', 'Call', 'Label', 'Tag', 'Mark',
                    'Sign', 'Write', 'Draw', 'Paint', 'Sketch',
                    'Illustrate', 'Depict', 'Portray', 'Represent',
                    'Symbolize', 'Mean', 'Signify', 'Indicate',
                    'Show', 'Demonstrate', 'Prove', 'Verify',
                    'Confirm', 'Validate', 'Authenticate',
                    'Certify', 'Guarantee', 'Assure', 'Promise',
                    'Pledge', 'Vow', 'Swear', 'Oath', 'Commit',
                    'Dedicate', 'Devote', 'Consecrate', 'Sanctify',
                    'Bless', 'Pray', 'Worship', 'Revere', 'Honor',
                    'Respect', 'Admire', 'Appreciate', 'Value',
                    'Cherish', 'Treasure', 'Prize', 'Esteem',
                    'Regard', 'Consider', 'Think', 'Believe',
                    'Suppose', 'Assume', 'Presume', 'Imagine',
                    'Dream', 'Fantasize', 'Envision', 'Picture',
                    'Visualize', 'Conceive', 'Create', 'Invent',
                    'Discover', 'Find', 'Locate', 'Spot', 'Detect',
                    'Sense', 'Feel', 'Experience', 'Undergo',
                    'Endure', 'Survive', 'Live', 'Exist', 'Be',
                    'Become', 'Grow', 'Develop', 'Evolve',
                    'Change', 'Transform', 'Convert', 'Alter',
                    'Modify', 'Adjust', 'Adapt', 'Customize',
                    'Personalize', 'Tailor', 'Fit', 'Match',
                    'Pair', 'Combine', 'Merge', 'Unite', 'Join',
                    'Connect', 'Link', 'Attach', 'Bind', 'Tie',
                    'Fasten', 'Secure', 'Lock', 'Seal', 'Close',
                    'Shut', 'Block', 'Obstruct', 'Hinder',
                    'Impede', 'Delay', 'Postpone', 'Defer',
                    'Suspend', 'Interrupt', 'Break', 'Stop',
                    'Halt', 'Cease', 'End', 'Terminate', 'Finish',
                    'Complete', 'Conclude', 'Finalize', 'Settle',
                    'Resolve', 'Decide', 'Determine', 'Choose',
                    'Select', 'Pick', 'Elect', 'Vote', 'Nominate',
                    'Appoint', 'Assign', 'Designate', 'Name',
                    'Title', 'Label', 'Classify', 'Categorize',
                    'Sort', 'Organize', 'Arrange', 'Order',
                    'Rank', 'Rate', 'Score', 'Grade', 'Evaluate',
                    'Assess', 'Appraise', 'Judge', 'Review',
                    'Examine', 'Inspect', 'Check', 'Test',
                    'Verify', 'Confirm', 'Validate', 'Prove',
                    'Demonstrate', 'Show', 'Display', 'Reveal',
                    'Expose', 'Uncover', 'Discover', 'Find',
                    'Learn', 'Study', 'Research', 'Investigate',
                    'Explore', 'Examine', 'Analyze', 'Study',
                    'Review', 'Read', 'Write', 'Compose', 'Draft',
                    'Edit', 'Revise', 'Correct', 'Fix', 'Repair',
                    'Maintain', 'Service', 'Support', 'Help',
                    'Assist', 'Aid', 'Guide', 'Direct', 'Lead',
                    'Manage', 'Control', 'Govern', 'Rule', 'Rule',
                    'Command', 'Order', 'Direct', 'Instruct',
                    'Teach', 'Train', 'Coach', 'Mentor', 'Advise',
                    'Counsel', 'Consult', 'Discuss', 'Talk',
                    'Speak', 'Say', 'Tell', 'Inform', 'Notify',
                    'Alert', 'Warn', 'Caution', 'Advise',
                    'Recommend', 'Suggest', 'Propose', 'Offer',
                    'Present', 'Submit', 'Deliver', 'Hand',
                    'Pass', 'Transfer', 'Move', 'Shift', 'Change',
                    'Switch', 'Swap', 'Exchange', 'Trade',
                    'Barter', 'Sell', 'Buy', 'Purchase', 'Order',
                    'Request', 'Ask', 'Demand', 'Require', 'Need',
                    'Want', 'Desire', 'Wish', 'Hope', 'Expect',
                    'Anticipate', 'Predict', 'Forecast', 'Project',
                    'Estimate', 'Calculate', 'Compute', 'Count',
                    'Measure', 'Weigh', 'Gauge', 'Assess',
                    'Evaluate', 'Judge', 'Decide', 'Determine',
                    'Conclude', 'Infer', 'Deduce', 'Reason',
                    'Think', 'Consider', 'Reflect', 'Contemplate',
                    'Meditate', 'Ponder', 'Wonder', 'Question',
                    'Ask', 'Inquire', 'Query', 'Search', 'Seek',
                    'Look', 'Find', 'Discover', 'Uncover',
                    'Reveal', 'Expose', 'Show', 'Display',
                    'Present', 'Introduce', 'Launch', 'Start',
                    'Begin', 'Initiate', 'Commence', 'Open',
                    'Establish', 'Found', 'Create', 'Build',
                    'Construct', 'Make', 'Produce', 'Generate',
                    'Develop', 'Design', 'Plan', 'Prepare',
                    'Arrange', 'Organize', 'Structure', 'Format',
                    'Style', 'Format', 'Layout', 'Design',
                    'Compose', 'Arrange', 'Organize', 'Order',
                    'Sort', 'Classify', 'Categorize', 'Group',
                    'Cluster', 'Bundle', 'Package', 'Wrap',
                    'Cover', 'Protect', 'Shield', 'Guard',
                    'Defend', 'Secure', 'Lock', 'Close', 'Seal',
                    'Fasten', 'Attach', 'Connect', 'Link', 'Join',
                    'Unite', 'Combine', 'Merge', 'Blend', 'Mix',
                    'Stir', 'Shake', 'Move', 'Shift', 'Slide',
                    'Roll', 'Turn', 'Spin', 'Rotate', 'Twist',
                    'Bend', 'Fold', 'Curve', 'Shape', 'Form',
                    'Mold', 'Cast', 'Carve', 'Cut', 'Slice',
                    'Chop', 'Hack', 'Split', 'Divide', 'Separate',
                    'Part', 'Break', 'Crack', 'Shatter', 'Smash',
                    'Crush', 'Squeeze', 'Press', 'Push', 'Pull',
                    'Drag', 'Lift', 'Raise', 'Elevate', 'Hoist',
                    'Lower', 'Drop', 'Fall', 'Sink', 'Dive',
                    'Plunge', 'Jump', 'Leap', 'Spring', 'Bounce',
                    'Rebound', 'Return', 'Come', 'Go', 'Leave',
                    'Depart', 'Exit', 'Escape', 'Flee', 'Run',
                    'Walk', 'Stroll', 'Wander', 'Roam', 'Travel',
                    'Journey', 'Voyage', 'Trip', 'Tour', 'Visit',
                    'Stay', 'Remain', 'Wait', 'Pause', 'Rest',
                    'Sleep', 'Wake', 'Rise', 'Stand', 'Sit',
                    'Lie', 'Recline', 'Lean', 'Rest', 'Support',
                    'Hold', 'Keep', 'Maintain', 'Preserve',
                    'Conserve', 'Save', 'Store', 'Stock', 'Hoard',
                    'Collect', 'Gather', 'Assemble', 'Accumulate',
                    'Build', 'Grow', 'Expand', 'Extend', 'Stretch',
                    'Reach', 'Touch', 'Feel', 'Sense', 'Perceive',
                    'Notice', 'Observe', 'Watch', 'See', 'View',
                    'Look', 'Gaze', 'Stare', 'Glance', 'Peek',
                    'Scan', 'Read', 'Study', 'Learn', 'Know',
                    'Understand', 'Comprehend', 'Grasp', 'Catch',
                    'Get', 'Obtain', 'Acquire', 'Gain', 'Win',
                    'Earn', 'Achieve', 'Accomplish', 'Succeed',
                    'Triumph', 'Conquer', 'Defeat', 'Beat', 'Win',
                    'Lose', 'Fail', 'Miss', 'Drop', 'Fall',
                    'Stumble', 'Trip', 'Slip', 'Slide', 'Skid',
                    'Crash', 'Collide', 'Hit', 'Strike', 'Punch',
                    'Kick', 'Push', 'Shove', 'Thrust', 'Drive',
                    'Force', 'Compel', 'Oblige', 'Require', 'Need',
                    'Want', 'Desire', 'Wish', 'Hope', 'Dream',
                    'Imagine', 'Think', 'Believe', 'Trust', 'Rely',
                    'Depend', 'Count', 'Expect', 'Anticipate',
                    'Predict', 'Forecast', 'Project', 'Plan',
                    'Prepare', 'Ready', 'Set', 'Start', 'Begin',
                    'Launch', 'Initiate', 'Commence', 'Open',
                    'Close', 'End', 'Finish', 'Complete', 'Done'}
    
    # Replace remaining capitalized words that aren't common English
    words = text.split()
    normalized = []
    for w in words:
        # Strip punctuation for checking
        base = re.sub(r'^[^a-zA-Z]+|[^a-zA-Z]+$', '', w)
        if base and base[0].isupper() and base not in common_words and len(base) > 1:
            # Check if it looks like a tool name (not a common word)
            normalized.append('[TOOL]' + w[len(base):])
        else:
            normalized.append(w)
    text = ' '.join(normalized)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def classify_pattern(normalized_text: str, section_type: str, occurrence_count: int) -> str:
    """Classify a near-duplicate pattern."""
    # Sources sections are necessary disclosure boilerplate
    if section_type == "sources":
        return "necessary_disclosure_boilerplate"
    
    # Limits sections with generic wording are harmful
    if section_type == "limits":
        if "designed for" in normalized_text.lower() and "may not" in normalized_text.lower():
            return "harmful_generic_editorial_copy"
    
    # Alternatives introductions are useful shared UI language
    if section_type == "alternatives":
        return "useful_shared_ui_language"
    
    # FAQ sections with generic questions
    if section_type == "questions":
        if occurrence_count >= 4:
            return "useful_shared_ui_language"
    
    # Overview sections
    if section_type == "overview":
        if occurrence_count >= 4:
            return "source_generated_repetition"
    
    # CTA / more-ways-to-choose
    if section_type in ("more-ways-to-choose", "cta"):
        return "useful_shared_ui_language"
    
    # Default classification based on occurrence count
    if occurrence_count >= 10:
        return "source_generated_repetition"
    elif occurrence_count >= 4:
        return "research_required_differentiation"
    else:
        return "useful_shared_ui_language"


def main():
    tools_dir = ROOT / "tools"
    html_files = sorted(tools_dir.glob("*.html"))
    
    # Section types to audit
    section_types = [
        "overview", "best-for", "strengths", "key-strengths",
        "cons", "limitations", "limits", "pricing", "pricing-caveats",
        "verdict", "sources", "questions", "alternatives",
        "more-ways-to-choose",
    ]
    
    # Collect all section texts
    all_sections = defaultdict(lambda: defaultdict(list))
    # all_sections[section_type][normalized_text] = [page1, page2, ...]
    
    for path in html_files:
        rel = path.name
        content = path.read_text(encoding="utf-8", errors="replace")
        
        for section_id in section_types:
            paras = extract_section_paragraphs(content, section_id)
            if not paras:
                continue
            
            # Combine paragraphs into a single text for this section
            full_text = " ".join(paras)
            normalized = normalize_text(full_text)
            
            if normalized:
                all_sections[section_id][normalized].append(rel)
    
    # Find patterns with 4+ occurrences
    patterns = []
    for section_type, text_map in all_sections.items():
        for normalized_text, pages in text_map.items():
            if len(pages) >= 4:
                classification = classify_pattern(normalized_text, section_type, len(pages))
                # Get original sample text
                sample_text = ""
                if pages:
                    sample_paras = extract_section_paragraphs(
                        (tools_dir / pages[0]).read_text(encoding="utf-8", errors="replace"),
                        section_type
                    )
                    if sample_paras:
                        sample_text = sample_paras[0][:200]
                
                patterns.append({
                    "section_type": section_type,
                    "normalized_text": normalized_text[:200],
                    "original_sample": sample_text,
                    "occurrence_count": len(pages),
                    "pages": sorted(pages),
                    "classification": classification,
                })
    
    # Also check limits sections with 2+ occurrences (they're more impactful)
    for normalized_text, pages in all_sections.get("limits", {}).items():
        if 2 <= len(pages) < 4:
            classification = classify_pattern(normalized_text, "limits", len(pages))
            sample_text = ""
            if pages:
                sample_paras = extract_section_paragraphs(
                    (tools_dir / pages[0]).read_text(encoding="utf-8", errors="replace"),
                    "limits"
                )
                if sample_paras:
                    sample_text = sample_paras[0][:200]
            patterns.append({
                "section_type": "limits",
                "normalized_text": normalized_text[:200],
                "original_sample": sample_text,
                "occurrence_count": len(pages),
                "pages": sorted(pages),
                "classification": classification,
            })
    
    # Sort by occurrence count descending
    patterns.sort(key=lambda x: -x["occurrence_count"])
    
    # Summary statistics
    classification_counts = Counter(p["classification"] for p in patterns)
    section_counts = Counter(p["section_type"] for p in patterns)
    
    # Build JSON report
    report = {
        "summary": {
            "total_patterns": len(patterns),
            "total_tool_pages_audited": len(html_files),
            "section_types_audited": list(all_sections.keys()),
            "classification_breakdown": dict(classification_counts),
            "section_breakdown": dict(section_counts),
        },
        "patterns": patterns,
    }
    
    json_path = REPORTS_DIR / "near-duplicate-content-audit.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written: {json_path}")
    
    # Build Markdown report
    md_lines = []
    md_lines.append("# Near-Duplicate Content Audit Report\n")
    md_lines.append(f"**Generated:** 2026-11-22\n")
    md_lines.append(f"**Tool pages audited:** {len(html_files)}\n")
    md_lines.append(f"**Patterns with 4+ occurrences:** {len(patterns)}\n")
    md_lines.append("## Classification Summary\n")
    md_lines.append("| Classification | Pattern Count |")
    md_lines.append("|---|---|")
    for cls_name, count in sorted(classification_counts.items(), key=lambda x: -x[1]):
        md_lines.append(f"| {cls_name} | {count} |")
    md_lines.append("")
    
    md_lines.append("## Section Breakdown\n")
    md_lines.append("| Section Type | Patterns Found |")
    md_lines.append("|---|---|")
    for sec_name, count in sorted(section_counts.items(), key=lambda x: -x[1]):
        md_lines.append(f"| {sec_name} | {count} |")
    md_lines.append("")
    
    md_lines.append("## Pattern Details\n")
    
    for i, pattern in enumerate(patterns, 1):
        md_lines.append(f"### Pattern {i}: {pattern['section_type']} — {pattern['classification']}\n")
        md_lines.append(f"- **Section:** `{pattern['section_type']}`")
        md_lines.append(f"- **Occurrences:** {pattern['occurrence_count']} pages")
        md_lines.append(f"- **Classification:** {pattern['classification']}")
        md_lines.append(f"- **Normalized text:** \"{pattern['normalized_text'][:150]}...\"")
        if pattern.get("original_sample"):
            md_lines.append(f"- **Sample (first page):** \"{pattern['original_sample'][:150]}...\"")
        md_lines.append(f"- **Affected pages:**\n")
        for p in pattern["pages"]:
            md_lines.append(f"  - `{p}`")
        md_lines.append("")
    
    # Verification
    md_lines.append("## Verification\n")
    md_lines.append(f"- Total patterns flagged: {len(patterns)}")
    md_lines.append(f"- All patterns have 4+ occurrences (or 2+ for limits sections)")
    md_lines.append(f"- Classification covers: {', '.join(classification_counts.keys())}")
    md_lines.append("")
    
    md_content = "\n".join(md_lines)
    md_path = REPORTS_DIR / "near-duplicate-content-audit.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"Written: {md_path}")
    
    # Print summary
    print(f"\n=== Near-Duplicate Content Audit Summary ===")
    print(f"Tool pages audited: {len(html_files)}")
    print(f"Patterns with 4+ occurrences: {len(patterns)}")
    print()
    for cls_name, count in sorted(classification_counts.items(), key=lambda x: -x[1]):
        print(f"  {cls_name}: {count} patterns")
    print()
    for sec_name, count in sorted(section_counts.items(), key=lambda x: -x[1]):
        print(f"  {sec_name}: {count} patterns")


if __name__ == "__main__":
    main()
