'use client'

import { useState } from 'react'
import { Search as SearchIcon, ExternalLink, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { api, SearchResult } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!query.trim()) {
      toast({
        title: 'Empty Query',
        description: 'Please enter a search query',
        variant: 'destructive',
      })
      return
    }

    setLoading(true)
    try {
      const response = await api.search(query, 20)
      setResults(response.results)
      
      if (response.results.length === 0) {
        toast({
          title: 'No Results',
          description: 'Try a different search query',
        })
      }
    } catch (error) {
      toast({
        title: 'Search Failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4">Search Learning Resources</h1>
          <p className="text-muted-foreground">
            Find articles, tutorials, and courses using semantic search
          </p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                type="text"
                placeholder="e.g., How to build a REST API with Python..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-10"
                disabled={loading}
              />
            </div>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <SearchIcon className="h-4 w-4 mr-2" />
                  Search
                </>
              )}
            </Button>
          </div>
        </form>

        {/* Results */}
        {results.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-semibold">
                Found {results.length} resources
              </h2>
            </div>

            {results.map((result) => (
              <Card key={result.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <CardTitle className="text-xl mb-2">
                        {result.title}
                      </CardTitle>
                      <CardDescription className="line-clamp-2">
                        {result.description}
                      </CardDescription>
                    </div>
                    <Badge variant="secondary">
                      {Math.round(result.score * 100)}% match
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex gap-2">
                      <Badge variant="outline">{result.type}</Badge>
                      {result.metadata?.difficulty && (
                        <Badge variant="outline">
                          {result.metadata.difficulty}
                        </Badge>
                      )}
                      {result.metadata?.duration && (
                        <Badge variant="outline">
                          {result.metadata.duration}
                        </Badge>
                      )}
                    </div>
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex"
                    >
                      <Button variant="ghost" size="sm" className="gap-2">
                        View Resource
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </a>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && results.length === 0 && query && (
          <Card className="text-center py-12">
            <CardContent>
              <SearchIcon className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No results found</h3>
              <p className="text-muted-foreground">
                Try adjusting your search query or use different keywords
              </p>
            </CardContent>
          </Card>
        )}

        {/* Initial State */}
        {!loading && results.length === 0 && !query && (
          <Card className="text-center py-12">
            <CardContent>
              <SearchIcon className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Start searching</h3>
              <p className="text-muted-foreground mb-4">
                Enter a topic or question to find relevant learning resources
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setQuery('machine learning basics')}
                >
                  Machine Learning
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setQuery('web development with React')}
                >
                  React Development
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setQuery('data structures and algorithms')}
                >
                  Data Structures
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
