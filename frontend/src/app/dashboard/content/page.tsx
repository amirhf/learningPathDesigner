'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2, Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react'

export default function ContentPage() {
  const [urls, setUrls] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const handleIngest = async () => {
    if (!urls.trim()) return

    setIsLoading(true)
    setStatus(null)

    try {
      const urlList = urls
        .split('\n')
        .map((u) => u.trim())
        .filter((u) => u.length > 0 && u.startsWith('http'))

      if (urlList.length === 0) {
        setStatus({ type: 'error', message: 'Please enter valid URLs (starting with http/https)' })
        setIsLoading(false)
        return
      }

      const result = await api.ingestContent(urlList)
      setStatus({ type: 'success', message: `Successfully started ingestion for ${result.count} URLs. They will appear in search shortly.` })
      setUrls('')
    } catch (error: any) {
      setStatus({ type: 'error', message: error.message || 'Failed to ingest content' })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Content Management</h1>
        <p className="text-muted-foreground">
          Add your own learning resources to the knowledge base.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Ingestion Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Ingest Resources
            </CardTitle>
            <CardDescription>
              Paste URLs of articles, blog posts, or documentation to add them to your personal library.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <textarea
              placeholder="https://example.com/article-1&#10;https://example.com/article-2"
              className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono"
              value={urls}
              onChange={(e) => {
                console.log('Textarea changed:', e.target.value);
                setUrls(e.target.value);
              }}
            />
            
            {status && (
              <Alert variant={status.type === 'success' ? 'default' : 'destructive'}>
                {status.type === 'success' ? <CheckCircle className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                <AlertTitle>{status.type === 'success' ? 'Success' : 'Error'}</AlertTitle>
                <AlertDescription>{status.message}</AlertDescription>
              </Alert>
            )}

            <Button 
              onClick={handleIngest} 
              disabled={isLoading || !urls.trim()} 
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Ingesting...
                </>
              ) : (
                'Start Ingestion'
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Info / Tips */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              How it works
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-muted-foreground">
            <p>
              When you add resources here, the system will:
            </p>
            <ul className="list-disc pl-5 space-y-2">
              <li>Fetch the content from each URL.</li>
              <li>Extract the main text and clean up formatting.</li>
              <li>Generate vector embeddings for semantic search.</li>
              <li>Associate the content with your <strong>Tenant ID</strong>.</li>
            </ul>
            <p className="mt-4">
              <strong>Note:</strong> Only you (and users in your tenant) will be able to see these resources in search results and generated plans.
            </p>
            <p>
              Processing typically takes 5-10 seconds per URL. Large batches may take longer.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
