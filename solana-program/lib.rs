use anchor_lang::prelude::*;

declare_id!("YourProgramIDHere");

#[program]
pub mod cyphervault {
    use super::*;

    // Share knowledge as NFT
    pub fn share_knowledge(
        ctx: Context<ShareKnowledge>,
        title: String,
        content_hash: String, // IPFS hash
        category: String,
    ) -> Result<()> {
        let knowledge = &mut ctx.accounts.knowledge;
        knowledge.owner = ctx.accounts.user.key();
        knowledge.title = title;
        knowledge.content_hash = content_hash;
        knowledge.category = category;
        knowledge.downloads = 0;
        knowledge.upvotes = 0;
        knowledge.created_at = Clock::get()?.unix_timestamp;
        Ok(())
    }

    // Upvote knowledge (costs tokens)
    pub fn upvote_knowledge(ctx: Context<UpvoteKnowledge>) -> Result<()> {
        let knowledge = &mut ctx.accounts.knowledge;
        knowledge.upvotes += 1;
        
        // Transfer tokens to knowledge owner as reward
        // ... token transfer logic ...
        
        Ok(())
    }

    // Download knowledge (costs tokens)
    pub fn download_knowledge(ctx: Context<DownloadKnowledge>) -> Result<()> {
        let knowledge = &mut ctx.accounts.knowledge;
        knowledge.downloads += 1;
        
        // Transfer tokens to knowledge owner
        // ... token transfer logic ...
        
        Ok(())
    }

    // ZKP verification on-chain
    pub fn verify_zkp(
        ctx: Context<VerifyZKP>,
        proof_hash: String,
    ) -> Result<()> {
        let zkp = &mut ctx.accounts.zkp;
        zkp.user = ctx.accounts.user.key();
        zkp.proof_hash = proof_hash;
        zkp.verified = true;
        zkp.timestamp = Clock::get()?.unix_timestamp;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct ShareKnowledge<'info> {
    #[account(init, payer = user, space = 8 + 500)]
    pub knowledge: Account<'info, Knowledge>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpvoteKnowledge<'info> {
    #[account(mut)]
    pub knowledge: Account<'info, Knowledge>,
    #[account(mut)]
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct DownloadKnowledge<'info> {
    #[account(mut)]
    pub knowledge: Account<'info, Knowledge>,
    #[account(mut)]
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct VerifyZKP<'info> {
    #[account(init, payer = user, space = 8 + 200)]
    pub zkp: Account<'info, ZKProof>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Knowledge {
    pub owner: Pubkey,
    pub title: String,
    pub content_hash: String, // IPFS hash of encrypted content
    pub category: String,
    pub downloads: u64,
    pub upvotes: u64,
    pub created_at: i64,
}

#[account]
pub struct ZKProof {
    pub user: Pubkey,
    pub proof_hash: String,
    pub verified: bool,
    pub timestamp: i64,
}