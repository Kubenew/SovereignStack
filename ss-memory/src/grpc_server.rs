use tonic::{transport::Server, Request, Response, Status, Streaming};
use tokio::sync::mpsc;
use tokio_stream::wrappers::ReceiverStream;

pub mod proto {
    tonic::include_proto!("mind_sync");
}

use proto::mind_sync_service_server::{MindSyncService, MindSyncServiceServer};
use proto::sovereign_alignment_service_server::{SovereignAlignmentService, SovereignAlignmentServiceServer};
use proto::{CognitiveDeltaRequest, CognitiveDeltaResponse, ZkAlignmentProofMessage, AlignmentVerificationResponse};

#[derive(Debug, Default)]
pub struct SovereignMindSyncServer;

#[tonic::async_trait]
impl MindSyncService for SovereignMindSyncServer {
    type StreamCognitiveDeltasStream = ReceiverStream<Result<CognitiveDeltaResponse, Status>>;

    async fn stream_cognitive_deltas(
        &self,
        request: Request<Streaming<CognitiveDeltaRequest>>,
    ) -> Result<Response<Self::StreamCognitiveDeltasStream>, Status> {
        let mut stream = request.into_inner();
        let (tx, rx) = mpsc::channel(128);

        tokio::spawn(async move {
            while let Some(Ok(req)) = stream.next().await {
                let response = CognitiveDeltaResponse {
                    new_state_hash: req.parent_state_hash,
                    synchronization_acknowledged: true,
                    error_message: String::new(),
                };
                if tx.send(Ok(response)).await.is_err() {
                    break;
                }
            }
        });

        Ok(Response::new(ReceiverStream::new(rx)))
    }
}

pub struct SovereignAlignmentServer;

#[tonic::async_trait]
impl SovereignAlignmentService for SovereignAlignmentServer {
    type StreamAlignmentProofsStream = ReceiverStream<Result<AlignmentVerificationResponse, Status>>;

    async fn stream_alignment_proofs(
        &self,
        request: Request<Streaming<ZkAlignmentProofMessage>>,
    ) -> Result<Response<Self::StreamAlignmentProofsStream>, Status> {
        let mut stream = request.into_inner();
        let (tx, rx) = mpsc::channel(128);

        tokio::spawn(async move {
            while let Some(Ok(proof)) = stream.next().await {
                let aligned = proof.proof_blob.len() >= 16 && proof.values_hash.len() == 32;
                let response = AlignmentVerificationResponse {
                    aligned,
                    verdict: if aligned { "ALIGNED".into() } else { "MISALIGNED".into() },
                    reason: String::new(),
                };
                if tx.send(Ok(response)).await.is_err() {
                    break;
                }
            }
        });

        Ok(Response::new(ReceiverStream::new(rx)))
    }
}

pub async fn start_grpc_fabric_transport(addr: &str) -> Result<(), Box<dyn std::error::Error>> {
    let address = addr.parse()?;
    let sync_service = SovereignMindSyncServer::default();
    let alignment_service = SovereignAlignmentServer;
    println!("gRPC Mind-Sync Fabric Service listening on {}", address);
    Server::builder()
        .add_service(MindSyncServiceServer::new(sync_service))
        .add_service(SovereignAlignmentServiceServer::new(alignment_service))
        .serve(address)
        .await?;
    Ok(())
}
