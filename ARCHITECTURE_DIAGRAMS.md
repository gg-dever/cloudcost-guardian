# CloudCost Guardian - Architecture Diagrams

## High-Level System Architecture

```mermaid
graph TB
    subgraph "Trigger Layer"
        EB[EventBridge Scheduler<br/>Daily @ 08:00 UTC]
    end

    subgraph "Processing Layer - AWS Lambda"
        CA[Cost Analyzer<br/>Python 3.11 | 256MB]
        FC[Forecaster<br/>Python 3.11 | 256MB]
        RC[Recommender<br/>Python 3.11 | 256MB]
        NT[Notifier<br/>Python 3.11 | 256MB]
    end

    subgraph "Data Layer - DynamoDB"
        CH[(cost_history<br/>PK: date<br/>SK: service_name)]
        AN[(cost_anomalies<br/>PK: anomaly_type<br/>SK: detection_date)]
        RE[(cost_recommendations<br/>PK: recommendation_type<br/>SK: generated_date)]
    end

    subgraph "AWS Services"
        CE[Cost Explorer API<br/>GetCostAndUsage<br/>GetCostForecast]
        SN[SNS Topic<br/>Email Alerts]
    end

    subgraph "Lambda Layer"
        LL[Shared Modules<br/>Schemas | Routers]
    end

    EB -->|Invokes| CA
    CA -->|Fetch Costs| CE
    CA -->|Write| CH
    CA -.->|Uses| LL

    FC -->|Query History| CH
    FC -->|Call Forecast API| CE
    FC -->|Write Forecasts| CH
    FC -.->|Uses| LL

    RC -->|Read Costs| CH
    RC -->|Write| RE
    RC -.->|Uses| LL

    NT -->|Query Costs| CH
    NT -->|Write| AN
    NT -->|Publish| SN
    NT -.->|Uses| LL

    SN -->|Email| U[📧 User]

    style EB fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff
    style CA fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff
    style FC fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff
    style RC fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff
    style NT fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff
    style CH fill:#4053D6,stroke:#232F3E,stroke-width:2px,color:#fff
    style AN fill:#4053D6,stroke:#232F3E,stroke-width:2px,color:#fff
    style RE fill:#4053D6,stroke:#232F3E,stroke-width:2px,color:#fff
    style CE fill:#759C3E,stroke:#232F3E,stroke-width:2px,color:#fff
    style SN fill:#C925D1,stroke:#232F3E,stroke-width:2px,color:#fff
    style LL fill:#146EB4,stroke:#232F3E,stroke-width:2px,color:#fff
```

## Data Flow Sequence

```mermaid
sequenceDiagram
    participant EB as EventBridge
    participant CA as Cost Analyzer
    participant CE as Cost Explorer API
    participant DB as cost_history
    participant FC as Forecaster
    participant RC as Recommender
    participant NT as Notifier
    participant SNS as SNS Topic
    participant User as 📧 User

    Note over EB: Daily @ 08:00 UTC
    EB->>CA: Trigger Lambda
    CA->>CE: GetCostAndUsage(last 30 days)
    CE-->>CA: Cost data by service
    CA->>DB: Store cost records

    Note over FC: Manual/Scheduled Trigger
    FC->>DB: Query historical costs
    FC->>CE: GetCostForecast(next 30 days)
    CE-->>FC: Forecast predictions
    FC->>DB: Store forecasts (service_name='FORECAST')

    Note over RC: Analyze patterns
    RC->>DB: Scan costs (exclude forecasts)
    RC->>RC: Generate recommendations
    RC->>DB: Store recommendations

    Note over NT: Check for anomalies
    NT->>DB: Query today's costs (exclude forecasts)
    NT->>NT: Detect anomalies
    alt Anomaly Detected
        NT->>DB: Store anomaly record
        NT->>SNS: Publish alert
        SNS->>User: Send email notification
    end
```

## Router Pattern Architecture

```mermaid
graph LR
    subgraph "Lambda Functions"
        L1[Cost Analyzer]
        L2[Forecaster]
        L3[Recommender]
        L4[Notifier]
    end

    subgraph "Lambda Layer - Routers"
        R1[cost_history_router<br/>14 methods]
        R2[cost_anomalies_router<br/>10 methods]
        R3[cost_recommendations_router<br/>12 methods]
    end

    subgraph "DynamoDB Tables"
        T1[(cost_history)]
        T2[(cost_anomalies)]
        T3[(cost_recommendations)]
    end

    L1 -->|Import| R1
    L2 -->|Import| R1
    L3 -->|Import| R1
    L3 -->|Import| R3
    L4 -->|Import| R1
    L4 -->|Import| R2

    R1 -.->|boto3| T1
    R2 -.->|boto3| T2
    R3 -.->|boto3| T3

    style R1 fill:#146EB4,stroke:#232F3E,stroke-width:2px,color:#fff
    style R2 fill:#146EB4,stroke:#232F3E,stroke-width:2px,color:#fff
    style R3 fill:#146EB4,stroke:#232F3E,stroke-width:2px,color:#fff
```

## DynamoDB Table Schema

```mermaid
erDiagram
    COST_HISTORY {
        string date PK
        string service_name SK
        decimal cost_usd
        decimal usage_quantity
        string confidence "for forecasts"
        int ttl "90 days"
    }

    COST_ANOMALIES {
        string anomaly_type PK
        string detection_date SK
        string severity
        string message
        string service_name
        decimal cost_usd
        int ttl "90 days"
    }

    COST_RECOMMENDATIONS {
        string recommendation_type PK
        string generated_date SK
        string service_name
        decimal current_cost
        decimal potential_savings
        string priority
        string status
        int ttl "180 days"
    }
```

## Cost Breakdown (Monthly)

```mermaid
pie title Monthly AWS Costs (~$2.75/month)
    "DynamoDB Storage & Requests" : 50
    "Lambda Invocations" : 20
    "Lambda Compute Time" : 15
    "SNS Notifications" : 10
    "CloudWatch Logs" : 5
```

## Deployment Pipeline

```mermaid
graph LR
    A[Local Development] -->|Push| B[Git Repository]
    B -->|Clone| C[Setup Environment]
    C -->|Run| D[setup-env.sh]
    D -->|Creates| E[Virtual Environment]
    E -->|Install| F[Dependencies]
    F -->|Execute| G[Terraform Init]
    G -->|Plan| H[Terraform Plan]
    H -->|Review| I[Terraform Apply]
    I -->|Deploy| J[AWS Resources]
    J -->|Confirm| K[SNS Subscription]
    K -->|Test| L[Lambda Invocation]
    L -->|✅| M[Production Ready]

    style A fill:#90EE90,stroke:#000,stroke-width:2px
    style M fill:#90EE90,stroke:#000,stroke-width:2px
```

## IAM Permission Model

```mermaid
graph TB
    subgraph "Lambda Execution Role"
        R[cloudcost-guardian-lambda-role]
    end

    subgraph "Policies Attached"
        P1[AWSLambdaBasicExecutionRole<br/>CloudWatch Logs]
        P2[DynamoDB Policy<br/>Read/Write all tables]
        P3[Cost Explorer Policy<br/>GetCostAndUsage<br/>GetCostForecast]
        P4[SNS Policy<br/>Publish to alerts topic]
    end

    subgraph "Resources Accessed"
        CW[CloudWatch Logs]
        DB1[(cost_history)]
        DB2[(cost_anomalies)]
        DB3[(cost_recommendations)]
        CE[Cost Explorer API]
        SNS[SNS Topic]
    end

    R -.->|Allows| P1
    R -.->|Allows| P2
    R -.->|Allows| P3
    R -.->|Allows| P4

    P1 -->|Write| CW
    P2 -->|Read/Write| DB1
    P2 -->|Read/Write| DB2
    P2 -->|Read/Write| DB3
    P3 -->|Read| CE
    P4 -->|Publish| SNS

    style R fill:#FF9900,stroke:#232F3E,stroke-width:3px,color:#fff
```

## How to Use These Diagrams

### For LinkedIn/Portfolio
1. **Take screenshots** of these diagrams and add them to your portfolio
2. **In presentations**: Use the high-level architecture diagram
3. **In interviews**: Walk through the data flow sequence

### For Technical Discussions
1. **System Design**: Show the high-level architecture
2. **Data Modeling**: Reference the DynamoDB schema
3. **Code Organization**: Explain the router pattern
4. **Security**: Walk through the IAM permission model

### Rendering Options

**GitHub/GitLab**: Mermaid renders automatically in markdown files

**LinkedIn**:
- Screenshot these diagrams
- Use tools like [Mermaid Live Editor](https://mermaid.live/)
- Export as PNG/SVG

**Portfolio Website**:
- Embed using mermaid.js library
- Or export as high-res images

**Presentations**:
- Export as SVG for crisp scaling
- Use white background for printing

---

## Diagram Sources

All diagrams are written in **Mermaid syntax** and can be:
- ✅ Rendered on GitHub automatically
- ✅ Edited in any text editor
- ✅ Version controlled with Git
- ✅ Exported to PNG/SVG/PDF

**Edit online**: https://mermaid.live/
**Documentation**: https://mermaid.js.org/

---

*These diagrams are designed for technical interviews and portfolio presentations.*
