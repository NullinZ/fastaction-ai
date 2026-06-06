export const cardGalleryGroups = [
  {
    key: 'protocol',
    name: 'Protocol Cards',
    nameZh: '协议核心卡片',
    scope: 'FastAction Core',
    description: 'Stable cards shipped by the engine. They are generic UI contracts, not business logic.',
    descriptionZh: '引擎内置的稳定卡片。它们是通用展示协议，不包含业务逻辑。',
    cards: [
      {
        type: 'list_card',
        name: 'List Card',
        nameZh: '列表卡',
        status: 'core',
        visual: 'list',
        purpose: 'Render list, search, count, and query results from an existing API.',
        purposeZh: '展示已有 API 返回的列表、搜索、数量和查询结果。',
        style: ['Compact header', 'Count badge', 'Three to five rows', 'Empty state'],
        styleZh: ['紧凑标题区', '数量标签', '三到五条列表行', '空状态'],
        fieldBindings: {
          title: '$.data.title',
          subtitle: '$.data.summary',
          items: '$.data.items',
          item_title: '$.title',
          item_subtitle: '$.owner_name',
          item_meta: '$.status_name'
        },
        cardDefinition: {
          card_type: 'list_card',
          name: { en: 'List card', zh: '列表卡' },
          category: 'protocol',
          data_contract: {
            type: 'object',
            required: ['title', 'items'],
            properties: {
              title: { type: 'string' },
              subtitle: { type: 'string' },
              items: { type: 'array' }
            }
          },
          states: ['loading', 'success', 'empty', 'error'],
          fallback: { card_type: 'generic_data_card' }
        },
        sampleResponse: {
          data: {
            title: 'Pending tasks',
            summary: '3 tasks require attention',
            items: [
              { id: 'task_001', title: 'Review contract', owner_name: 'Maya', status_name: 'Due today' },
              { id: 'task_002', title: 'Confirm installation date', owner_name: 'Alex', status_name: 'Open' },
              { id: 'task_003', title: 'Upload site photos', owner_name: 'Jordan', status_name: 'Waiting' }
            ]
          }
        }
      },
      {
        type: 'detail_card',
        name: 'Detail Card',
        nameZh: '详情卡',
        status: 'core',
        visual: 'detail',
        purpose: 'Show one business record with important attributes and optional actions.',
        purposeZh: '展示一条业务记录的关键属性和可选操作。',
        style: ['Title first', 'Two-column rows', 'Readable values', 'Optional footer action'],
        styleZh: ['标题优先', '双列属性行', '值易读', '可选底部动作'],
        fieldBindings: {
          title: '$.data.name',
          subtitle: '$.data.code',
          rows: '$.data.rows'
        },
        cardDefinition: {
          card_type: 'detail_card',
          name: { en: 'Detail card', zh: '详情卡' },
          category: 'protocol',
          data_contract: {
            type: 'object',
            required: ['title'],
            properties: {
              title: { type: 'string' },
              subtitle: { type: 'string' },
              rows: { type: 'array' }
            }
          },
          states: ['loading', 'success', 'empty', 'error'],
          fallback: { card_type: 'generic_data_card' }
        },
        sampleResponse: {
          data: {
            name: 'Customer account',
            code: 'ACME-2026',
            rows: [
              { label: 'Status', value: 'Active' },
              { label: 'Owner', value: 'Maya Chen' },
              { label: 'Last update', value: '2026-06-06 10:24' }
            ]
          }
        }
      },
      {
        type: 'metric_card',
        name: 'Metric Card',
        nameZh: '指标卡',
        status: 'core',
        visual: 'metric',
        purpose: 'Render count, aggregate, score, and trend results.',
        purposeZh: '展示数量、聚合、评分和趋势类结果。',
        style: ['Large value', 'Short label', 'Trend text', 'No dense table'],
        styleZh: ['大数字', '短标签', '趋势文本', '不堆表格'],
        fieldBindings: {
          label: '$.data.label',
          value: '$.data.value',
          trend: '$.data.trend',
          tone: '$.data.tone'
        },
        cardDefinition: {
          card_type: 'metric_card',
          name: { en: 'Metric card', zh: '指标卡' },
          category: 'protocol',
          data_contract: {
            type: 'object',
            required: ['label', 'value'],
            properties: {
              label: { type: 'string' },
              value: {},
              trend: { type: 'string' },
              tone: { type: 'string' }
            }
          },
          states: ['loading', 'success', 'empty', 'error'],
          fallback: { card_type: 'generic_data_card' }
        },
        sampleResponse: {
          data: {
            label: 'Open tickets',
            value: 27,
            trend: '+4 this week',
            tone: 'warning'
          }
        }
      },
      {
        type: 'result_card',
        name: 'Result Card',
        nameZh: '结果卡',
        status: 'core',
        visual: 'result',
        purpose: 'Render completion, failure, partial success, and execution summaries.',
        purposeZh: '展示完成、失败、部分成功和执行摘要。',
        style: ['Status badge', 'Clear result title', 'Short message', 'Trace-friendly metadata'],
        styleZh: ['状态标签', '清晰结果标题', '短说明', '便于 Trace 的元数据'],
        fieldBindings: {
          status: '$.data.status',
          title: '$.data.title',
          message: '$.data.message',
          reference_id: '$.data.reference_id'
        },
        cardDefinition: {
          card_type: 'result_card',
          name: { en: 'Result card', zh: '结果卡' },
          category: 'protocol',
          data_contract: {
            type: 'object',
            required: ['status', 'title'],
            properties: {
              status: { type: 'string' },
              title: { type: 'string' },
              message: { type: 'string' },
              reference_id: { type: 'string' }
            }
          },
          states: ['success', 'partial', 'error'],
          fallback: { card_type: 'generic_data_card' }
        },
        sampleResponse: {
          data: {
            status: 'success',
            title: 'Upload completed',
            message: '3 attachments were linked to the record.',
            reference_id: 'run_01HX'
          }
        }
      },
      {
        type: 'confirm_card',
        name: 'Confirm Card',
        nameZh: '确认卡',
        status: 'core',
        visual: 'confirm',
        purpose: 'Ask for explicit confirmation before write, destructive, or high-risk actions.',
        purposeZh: '在写入、破坏性或高风险动作前请求用户明确确认。',
        style: ['Risk label', 'Action summary', 'Parameter preview', 'Primary and secondary actions'],
        styleZh: ['风险标签', '动作摘要', '参数预览', '主次按钮'],
        fieldBindings: {
          title: '$.data.title',
          action: '$.data.action',
          params: '$.data.params',
          risk: '$.data.risk'
        },
        cardDefinition: {
          card_type: 'confirm_card',
          name: { en: 'Confirm card', zh: '确认卡' },
          category: 'protocol',
          data_contract: {
            type: 'object',
            required: ['title', 'action'],
            properties: {
              title: { type: 'string' },
              action: { type: 'string' },
              risk: { type: 'string' },
              params: { type: 'object' }
            }
          },
          states: ['pending', 'confirmed', 'cancelled'],
          fallback: { card_type: 'generic_data_card' }
        },
        sampleResponse: {
          data: {
            title: 'Confirm write action',
            action: 'Create a site record and attach 3 files',
            risk: 'write',
            params: { record_type: 'site_update', attachment_count: 3 }
          }
        }
      },
      {
        type: 'picker_card',
        name: 'Picker Card',
        nameZh: '选择卡',
        status: 'core',
        visual: 'picker',
        purpose: 'Resolve ambiguous entities or let the user choose from allowed context options.',
        purposeZh: '在实体不确定时让用户从允许的上下文候选中选择。',
        style: ['Prompt title', 'Candidate list', 'Confidence/meta', 'Single clear selection'],
        styleZh: ['提示标题', '候选列表', '置信度/元信息', '单一明确选择'],
        fieldBindings: {
          title: '$.data.title',
          options: '$.data.options',
          option_label: '$.label',
          option_value: '$.value'
        },
        cardDefinition: {
          card_type: 'picker_card',
          name: { en: 'Picker card', zh: '选择卡' },
          category: 'protocol',
          data_contract: {
            type: 'object',
            required: ['title', 'options'],
            properties: {
              title: { type: 'string' },
              options: { type: 'array' }
            }
          },
          states: ['missing_params', 'ambiguous', 'selected'],
          fallback: { card_type: 'generic_data_card' }
        },
        sampleResponse: {
          data: {
            title: 'Choose the workspace',
            options: [
              { value: 'ws_101', label: 'Workspace Alpha', meta: 'active' },
              { value: 'ws_102', label: 'Workspace Beta', meta: 'recent' }
            ]
          }
        }
      },
      {
        type: 'missing_params_card',
        name: 'Missing Parameters Card',
        nameZh: '缺参卡',
        status: 'core',
        visual: 'missing',
        purpose: 'Show exactly which required parameters are missing after an API has been matched.',
        purposeZh: '在已经命中 API 后，明确展示缺少哪些必填参数。',
        style: ['Matched API', 'Missing field label and name', 'Source hint', 'Template action'],
        styleZh: ['已命中 API', '缺失字段名称', '来源提示', '模板动作'],
        fieldBindings: {
          api_id: '$.api.id',
          missing_param_details: '$.clarify.missing_param_details',
          pending_instruction: '$.pending_instruction'
        },
        cardDefinition: {
          card_type: 'missing_params_card',
          name: { en: 'Missing parameters card', zh: '缺参卡' },
          category: 'protocol',
          data_contract: {
            type: 'object',
            required: ['missing_param_details'],
            properties: {
              api_id: { type: 'string' },
              missing_param_details: { type: 'array' },
              pending_instruction: { type: 'object' }
            }
          },
          states: ['missing_params'],
          fallback: { card_type: 'generic_data_card' }
        },
        sampleResponse: {
          api: { id: 'records.create_note', name: 'Create note' },
          clarify: {
            missing_param_details: [
              {
                name: 'record_id',
                label: { en: 'Record', zh: '记录' },
                type: 'string',
                source: 'context.record_id | params.record_id',
                resolve_entity: 'records'
              },
              {
                name: 'content',
                label: { en: 'Content', zh: '内容' },
                type: 'string',
                source: 'params.content'
              }
            ]
          }
        }
      },
      {
        type: 'generic_data_card',
        name: 'Generic Data Card',
        nameZh: '通用数据卡',
        status: 'core',
        visual: 'json',
        purpose: 'Fallback renderer for unknown or newly registered card types.',
        purposeZh: '未知卡片或新注册卡片的兜底渲染器。',
        style: ['Plain title', 'JSON preview', 'Safe fallback', 'Developer-oriented'],
        styleZh: ['普通标题', 'JSON 预览', '安全兜底', '开发者友好'],
        fieldBindings: {
          title: '$.data.title',
          payload: '$.data'
        },
        cardDefinition: {
          card_type: 'generic_data_card',
          name: { en: 'Generic data card', zh: '通用数据卡' },
          category: 'protocol',
          data_contract: {
            type: 'object',
            properties: {}
          },
          states: ['success', 'empty', 'error'],
          fallback: { card_type: 'generic_data_card' }
        },
        sampleResponse: {
          data: {
            title: 'Raw response',
            payload: {
              status: 'ok',
              count: 2
            }
          }
        }
      }
    ]
  },
  {
    key: 'business',
    name: 'Business Examples',
    nameZh: '企业业务样例',
    scope: 'Examples',
    description: 'Reusable examples for common enterprise systems. They demonstrate patterns and can be copied or renamed by host applications.',
    descriptionZh: '常见企业系统可复用样例。它们用于展示模式，宿主系统可复制后改名使用。',
    cards: [
      {
        type: 'todo_card',
        name: 'Todo Card',
        nameZh: '待办卡',
        status: 'example',
        visual: 'list',
        purpose: 'Show tasks a user should handle next.',
        purposeZh: '展示用户下一步需要处理的任务。',
        style: ['Priority signal', 'Due date', 'Compact action list'],
        styleZh: ['优先级提示', '截止时间', '紧凑动作列表'],
        fieldBindings: {
          title: 'Today todos',
          items: '$.data.todos',
          item_title: '$.title',
          item_meta: '$.priority_name'
        },
        cardDefinition: {
          card_type: 'todo_card',
          name: { en: 'Todo card', zh: '待办卡' },
          category: 'business_example',
          data_contract: { type: 'object', required: ['items'], properties: { items: { type: 'array' } } },
          states: ['success', 'empty', 'error'],
          fallback: { card_type: 'list_card' }
        },
        sampleResponse: {
          data: {
            todos: [
              { id: 'todo_1', title: 'Approve the quote', priority_name: 'High · today' },
              { id: 'todo_2', title: 'Reply to customer question', priority_name: 'Normal' }
            ]
          }
        }
      },
      {
        type: 'progress_card',
        name: 'Progress Card',
        nameZh: '进度卡',
        status: 'example',
        visual: 'progress',
        purpose: 'Show project, order, ticket, or workflow progress.',
        purposeZh: '展示项目、订单、工单或流程进度。',
        style: ['Percent focus', 'Milestones', 'Risk hint'],
        styleZh: ['进度百分比突出', '里程碑', '风险提示'],
        fieldBindings: {
          title: '$.data.name',
          percent: '$.data.progress.percent',
          phase: '$.data.progress.phase',
          milestones: '$.data.milestones'
        },
        cardDefinition: {
          card_type: 'progress_card',
          name: { en: 'Progress card', zh: '进度卡' },
          category: 'business_example',
          data_contract: { type: 'object', required: ['title', 'percent'], properties: {} },
          states: ['success', 'empty', 'error'],
          fallback: { card_type: 'metric_card' }
        },
        sampleResponse: {
          data: {
            name: 'Implementation project',
            progress: { percent: 64, phase: 'Delivery' },
            milestones: ['Requirement confirmed', 'Build in progress', 'Acceptance next']
          }
        }
      },
      {
        type: 'attachment_result_card',
        name: 'Attachment Result Card',
        nameZh: '附件结果卡',
        status: 'example',
        visual: 'attachment',
        purpose: 'Show uploaded drawings, contracts, media, or other file artifacts.',
        purposeZh: '展示已上传的文件、合同、媒体或其他附件资产。',
        style: ['File count', 'Thumbnail-ready', 'Result summary'],
        styleZh: ['文件数量', '可接缩略图', '结果摘要'],
        fieldBindings: {
          title: '$.data.title',
          files: '$.data.files',
          file_name: '$.name',
          file_url: '$.url'
        },
        cardDefinition: {
          card_type: 'attachment_result_card',
          name: { en: 'Attachment result card', zh: '附件结果卡' },
          category: 'business_example',
          data_contract: { type: 'object', required: ['files'], properties: { files: { type: 'array' } } },
          states: ['success', 'empty', 'error'],
          fallback: { card_type: 'result_card' }
        },
        sampleResponse: {
          data: {
            title: 'Files uploaded',
            files: [
              { id: 'file_1', name: 'floor-plan.png', url: 'https://example.com/files/floor-plan.png' },
              { id: 'file_2', name: 'site-photo.jpg', url: 'https://example.com/files/site-photo.jpg' }
            ]
          }
        }
      },
      {
        type: 'activity_feed_card',
        name: 'Activity Feed Card',
        nameZh: '动态记录卡',
        status: 'example',
        visual: 'feed',
        purpose: 'Show recent field records, customer updates, issue notes, or operational activity.',
        purposeZh: '展示现场记录、客户更新、问题备注或运营动态。',
        style: ['Chronological rows', 'Author/date meta', 'Attachment count'],
        styleZh: ['时间顺序行', '作者/日期元信息', '附件数量'],
        fieldBindings: {
          title: '$.data.title',
          items: '$.data.records',
          item_title: '$.title',
          item_meta: '$.created_at'
        },
        cardDefinition: {
          card_type: 'activity_feed_card',
          name: { en: 'Activity feed card', zh: '动态记录卡' },
          category: 'business_example',
          data_contract: { type: 'object', required: ['items'], properties: {} },
          states: ['success', 'empty', 'error'],
          fallback: { card_type: 'list_card' }
        },
        sampleResponse: {
          data: {
            title: 'Latest updates',
            records: [
              { title: 'Materials arrived', created_at: '2026-06-06 09:10' },
              { title: 'Inspection photo uploaded', created_at: '2026-06-06 11:30' }
            ]
          }
        }
      },
      {
        type: 'risk_alert_card',
        name: 'Risk Alert Card',
        nameZh: '风险提醒卡',
        status: 'example',
        visual: 'risk',
        purpose: 'Highlight delays, budget exceptions, compliance risks, and blocked work.',
        purposeZh: '突出延期、预算异常、合规风险和阻塞事项。',
        style: ['Severity badge', 'Cause', 'Suggested action'],
        styleZh: ['严重级别标签', '原因', '建议动作'],
        fieldBindings: {
          title: '$.data.title',
          level: '$.data.level',
          reason: '$.data.reason',
          actions: '$.data.actions'
        },
        cardDefinition: {
          card_type: 'risk_alert_card',
          name: { en: 'Risk alert card', zh: '风险提醒卡' },
          category: 'business_example',
          data_contract: { type: 'object', required: ['title', 'level'], properties: {} },
          states: ['success', 'empty', 'error'],
          fallback: { card_type: 'result_card' }
        },
        sampleResponse: {
          data: {
            title: 'Delivery risk detected',
            level: 'medium',
            reason: 'Vendor response is overdue by 2 days.',
            actions: ['Contact vendor', 'Notify owner']
          }
        }
      },
      {
        type: 'daily_brief_card',
        name: 'Daily Brief Card',
        nameZh: '每日简报卡',
        status: 'example',
        visual: 'brief',
        purpose: 'Summarize daily work, changes, blockers, and recommended next actions.',
        purposeZh: '总结每日工作、变化、阻塞和建议动作。',
        style: ['Three key points', 'Metric strip', 'Next action'],
        styleZh: ['三个重点', '指标条', '下一步动作'],
        fieldBindings: {
          title: '$.data.title',
          metrics: '$.data.metrics',
          items: '$.data.highlights',
          next_action: '$.data.next_action'
        },
        cardDefinition: {
          card_type: 'daily_brief_card',
          name: { en: 'Daily brief card', zh: '每日简报卡' },
          category: 'business_example',
          data_contract: { type: 'object', required: ['highlights'], properties: {} },
          states: ['success', 'empty', 'error'],
          fallback: { card_type: 'list_card' }
        },
        sampleResponse: {
          data: {
            title: 'Daily brief',
            metrics: [{ label: 'Open', value: 12 }, { label: 'Done', value: 8 }],
            highlights: ['Two tickets closed', 'One approval waiting', 'No critical incident'],
            next_action: 'Review overdue approvals'
          }
        }
      }
    ]
  },
  {
    key: 'host-ui',
    name: 'Host UI Samples',
    nameZh: '宿主 UI 样例',
    scope: 'Host Adapter',
    description: 'Patterns host applications may keep outside FastAction but still document beside their adapter.',
    descriptionZh: '宿主系统可以保留在 FastAction 外部，但应在 Adapter 文档旁说明的 UI 模式。',
    cards: [
      {
        type: 'chat_message_card',
        name: 'Chat Message Card',
        nameZh: '聊天消息卡',
        status: 'host',
        visual: 'chat',
        purpose: 'Render user and assistant messages around FastAction instructions.',
        purposeZh: '在 FastAction 指令外围渲染用户和助手消息。',
        style: ['Role-based alignment', 'Readable text', 'Attachment area'],
        styleZh: ['按角色对齐', '文本易读', '附件区域'],
        fieldBindings: {
          role: '$.message.role',
          content: '$.message.content',
          attachments: '$.message.attachments'
        },
        cardDefinition: {
          card_type: 'chat_message_card',
          name: { en: 'Chat message card', zh: '聊天消息卡' },
          category: 'host_ui_sample',
          data_contract: { type: 'object', required: ['role', 'content'], properties: {} },
          states: ['streaming', 'success', 'error'],
          fallback: { card_type: 'generic_data_card' }
        },
        sampleResponse: {
          message: {
            role: 'assistant',
            content: 'I found the matching capability and need one more parameter.',
            attachments: []
          }
        }
      },
      {
        type: 'attachment_preview_card',
        name: 'Attachment Preview Card',
        nameZh: '附件预览卡',
        status: 'host',
        visual: 'attachment',
        purpose: 'Preview files before a host application uploads or submits them.',
        purposeZh: '在宿主系统上传或提交附件前预览文件。',
        style: ['Thumbnail slot', 'File type', 'Remove action'],
        styleZh: ['缩略图位', '文件类型', '移除动作'],
        fieldBindings: {
          files: '$.attachments',
          file_name: '$.name',
          mime_type: '$.mime_type'
        },
        cardDefinition: {
          card_type: 'attachment_preview_card',
          name: { en: 'Attachment preview card', zh: '附件预览卡' },
          category: 'host_ui_sample',
          data_contract: { type: 'object', required: ['files'], properties: {} },
          states: ['ready', 'uploading', 'error'],
          fallback: { card_type: 'generic_data_card' }
        },
        sampleResponse: {
          attachments: [
            { id: 'att_1', name: 'photo.jpg', mime_type: 'image/jpeg' },
            { id: 'att_2', name: 'document.pdf', mime_type: 'application/pdf' }
          ]
        }
      },
      {
        type: 'quick_action_chip',
        name: 'Quick Action Chip',
        nameZh: '快捷动作卡',
        status: 'host',
        visual: 'chips',
        purpose: 'Offer common prompts or shortcuts before the user types a full request.',
        purposeZh: '在用户完整输入前提供常用问题或快捷入口。',
        style: ['Short label', 'Single tap', 'Prompt text payload'],
        styleZh: ['短标签', '单次点击', '携带 Prompt 文本'],
        fieldBindings: {
          label: '$.label',
          prompt: '$.prompt',
          metadata: '$.metadata'
        },
        cardDefinition: {
          card_type: 'quick_action_chip',
          name: { en: 'Quick action chip', zh: '快捷动作卡' },
          category: 'host_ui_sample',
          data_contract: { type: 'object', required: ['label', 'prompt'], properties: {} },
          states: ['ready', 'selected'],
          fallback: { card_type: 'generic_data_card' }
        },
        sampleResponse: {
          label: 'Show my tasks',
          prompt: 'Show my pending tasks for this workspace.',
          metadata: { source: 'home_shortcut' }
        }
      },
      {
        type: 'notification_item_card',
        name: 'Notification Item Card',
        nameZh: '通知项卡',
        status: 'host',
        visual: 'notification',
        purpose: 'Render host notifications that may link into FastAction-enabled workflows.',
        purposeZh: '展示可跳转到 FastAction 相关流程的宿主通知。',
        style: ['Unread state', 'Title and body', 'Time meta'],
        styleZh: ['未读状态', '标题正文', '时间元信息'],
        fieldBindings: {
          title: '$.title',
          body: '$.body',
          created_at: '$.created_at',
          read: '$.read'
        },
        cardDefinition: {
          card_type: 'notification_item_card',
          name: { en: 'Notification item card', zh: '通知项卡' },
          category: 'host_ui_sample',
          data_contract: { type: 'object', required: ['title'], properties: {} },
          states: ['read', 'unread'],
          fallback: { card_type: 'generic_data_card' }
        },
        sampleResponse: {
          title: 'Approval required',
          body: 'A workflow is waiting for your confirmation.',
          created_at: '2026-06-06 14:05',
          read: false
        }
      }
    ]
  }
]

export function cardRenderConfig(card) {
  return {
    card_type: card.type,
    fallback_card_type: card.cardDefinition?.fallback?.card_type || 'generic_data_card',
    field_bindings: card.fieldBindings
  }
}

export function cardSnippet(card, kind) {
  if (kind === 'definition') return JSON.stringify(card.cardDefinition, null, 2)
  if (kind === 'render') return JSON.stringify(cardRenderConfig(card), null, 2)
  if (kind === 'response') return JSON.stringify(card.sampleResponse, null, 2)
  return JSON.stringify(card, null, 2)
}

export function flattenCards() {
  return cardGalleryGroups.flatMap(group =>
    group.cards.map(card => ({
      ...card,
      groupKey: group.key,
      groupName: group.name,
      groupNameZh: group.nameZh,
      groupScope: group.scope
    }))
  )
}
