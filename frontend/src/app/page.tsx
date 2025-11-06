'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Search, Target, GraduationCap, Sparkles, Clock, TrendingUp } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-12">
      {/* Hero Section */}
      <section className="text-center mb-16">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary mb-6">
          <Sparkles className="h-4 w-4" />
          <span className="text-sm font-medium">AI-Powered Learning</span>
        </div>
        
        <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
          Design Your Learning Path
        </h1>
        
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          Get personalized learning plans tailored to your goals, time budget, and skill level.
          Powered by AI and curated resources.
        </p>
        
        <div className="flex gap-4 justify-center">
          <Link href="/plan/new">
            <Button size="lg" className="gap-2">
              <Target className="h-5 w-5" />
              Create Learning Plan
            </Button>
          </Link>
          <Link href="/search">
            <Button size="lg" variant="outline" className="gap-2">
              <Search className="h-5 w-5" />
              Explore Resources
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="mb-16">
        <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
        
        <div className="grid md:grid-cols-3 gap-8">
          <Card>
            <CardHeader>
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Target className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>Set Your Goal</CardTitle>
              <CardDescription>
                Tell us what you want to learn and your available time budget
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Our AI analyzes your goal and creates a structured learning path with
                milestones and resources.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Search className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>Curated Resources</CardTitle>
              <CardDescription>
                Get relevant articles, videos, and tutorials from trusted sources
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                We use semantic search to find the best learning materials matched to
                your specific needs.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <GraduationCap className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>Test Your Knowledge</CardTitle>
              <CardDescription>
                Take AI-generated quizzes to verify your understanding
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Each lesson includes a quiz with questions directly cited from the
                learning materials.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Benefits */}
      <section className="mb-16">
        <div className="bg-secondary/50 rounded-2xl p-12">
          <h2 className="text-3xl font-bold text-center mb-12">Why Choose LearnPath?</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <Clock className="h-8 w-8 text-primary" />
              </div>
              <h3 className="font-semibold mb-2">Time-Optimized</h3>
              <p className="text-sm text-muted-foreground">
                Plans adapt to your schedule and learning pace
              </p>
            </div>

            <div className="text-center">
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <h3 className="font-semibold mb-2">AI-Powered</h3>
              <p className="text-sm text-muted-foreground">
                Intelligent recommendations based on your progress
              </p>
            </div>

            <div className="text-center">
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="h-8 w-8 text-primary" />
              </div>
              <h3 className="font-semibold mb-2">Track Progress</h3>
              <p className="text-sm text-muted-foreground">
                Monitor your learning journey and achievements
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="text-center">
        <Card className="border-2 border-primary/20">
          <CardHeader>
            <CardTitle className="text-3xl">Ready to Start Learning?</CardTitle>
            <CardDescription className="text-lg">
              Create your first personalized learning plan in minutes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/plan/new">
              <Button size="lg" className="gap-2">
                <Target className="h-5 w-5" />
                Get Started Now
              </Button>
            </Link>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
