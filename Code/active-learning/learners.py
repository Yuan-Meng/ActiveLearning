
import random
import utils
import world
import entropy_gains
import low_model as model
import numpy as np
import AnalyzedData

class ActiveLearner(object):
	"""docstring for ActiveLearner"""
	def __init__(self):
		self.experience=[]
		
	def choose_action(self, prev_data=[]):#None):
		mingain=1000
		astars=[]
		for a in world.possible_actions():
			if len(prev_data)>0:
				if a==prev_data[-1].action:
					continue
			this_gain=self.expected_final_entropy(a, prev_data)
			if this_gain < mingain:
				astars=[a]
				mingain=this_gain
			elif this_gain == mingain:
				astars.append(a)
		#while True:
		#	print astars, prev_data[-1].action
		choice=random.choice(astars)
		#	if len(prev_data)==0:
		#		break
		#	elif choice!=prev_data[-1].action:
		#		break
		#self.experience.append(world.make_action(choice))
		return choice

	def choose_actions(self, prev_data=[]):
		"""
		Same as choose actions, but return all equivalents
		"""
		mingain=1000
		astars=[]
		for a in world.possible_actions():
			if len(prev_data)>0:
				if a==prev_data[-1].action:
					continue
			this_gain=self.expected_final_entropy(a, prev_data)
			if this_gain < mingain:
				astars=[a]
				mingain=this_gain
			elif this_gain == mingain:
				astars.append(a)
		return astars, mingain





	def choose_action_phase2(self, stage, prev_data):
		maxratio=0
		astars=[]

		selector={'a': world.possible_actions_phase2a, 'b': world.possible_actions_phase2b}
		possible_actions=selector[stage]()

		for a in possible_actions:
			dt=world.make_forced_action(a,True)
			df=world.make_forced_action(a,False)
			pt=model.p_data_action(dt,a,prev_data)
			pf=model.p_data_action(df,a,prev_data)
			print a, pt, pf, pt/pf
			this_ratio=pt/pf
			if this_ratio > maxratio:
				astars=[a]
				maxratio=this_ratio
			elif this_ratio == maxratio:
				astars.append(a)

		#print astars
		choice=random.choice(astars)
		return choice



	def play(self, n_actions):
		for i in range(n_actions):
			self.choose_action(self.experience)
		return self.experience


class RandomLearner(ActiveLearner):
	"""docstring for RandomLearner"""
	def __init__(self):
		super(RandomLearner, self).__init__()
		
		
	def expected_final_entropy(self, action, data=None):
		return 0 #all equivalent!


class TheoryLearner(ActiveLearner):
	"""docstring for TheoryLearner"""
	def __init__(self):
		super(TheoryLearner, self).__init__()
		
	
	def expected_final_entropy(self, action, data=None):
		#print entropy_gains.theory_entropy_gain(action, data)
		return entropy_gains.theory_expected_final_entropy(action, data)
	

	def expected_information_gain(self, action, data=None):
		return entropy_gains.theory_expected_entropy_gain(action, data)


class JointLearner(ActiveLearner):
	"""docstring for JointLearner"""
	def __init__(self):
		super(JointLearner, self).__init__()
		
		
	def expected_final_entropy(self, action, data=None):
		return entropy_gains.joint_expected_final_entropy(action, data)


class HypothesesLearner(ActiveLearner):
	"""docstring for HypothesesLearner"""
	def __init__(self):
		super(HypothesesLearner, self).__init__()
		
		
	def expected_final_entropy(self, action, data=None):
		return entropy_gains.hypotheses_expected_final_entropy(action, data)


class ActivePlayer():

	#def __init__(self):
		#self.experience=[]

	def choose_action(self, prev_data=[]):
		#mingain=1000
		maxprob=0
		astars=[]
		for a in world.possible_actions():
			if len(prev_data)>0:
				if a==prev_data[-1].action:
					continue
			#this_gain=self.expected_final_entropy(a, prev_data)
			this_prob=self.success_probability(a, prev_data)
			if this_prob > maxprob:
				astars=[a]
				maxprob=this_prob
				#mingain=this_gain
			#elif this_gain == mingain:
			elif this_prob == maxprob:
				astars.append(a)
		choice=random.choice(astars)
		#self.experience.append(world.make_action(choice))
		return choice

	def choose_actions(self, prev_data=[]):
		"""
		Same as choose actions, but return all equivalents
		"""
		maxprob=0
		astars=[]
		for a in world.possible_actions():
			if len(prev_data)>0:
				if a==prev_data[-1].action:
					continue
			this_prob=self.success_probability(a, prev_data)
			if this_prob > maxprob:
				astars=[a]
				maxprob=this_prob
			elif this_prob == maxprob:
				astars.append(a)
		#choice=random.choice(astars)
		return astars, maxprob



	def success_probability(self, action, prev_data=[]):

		data_no, data_yes=world.possible_data(action)
		p_yes=model.p_data_action(data_yes, action, prev_data)
		p_no=model.p_data_action(data_no, action, prev_data)
		
		return p_yes/(p_yes+p_no)



class TabulatedMixedLearner():
	
	""" 
	Player mixing IG and PM with probability theta (for IG). 
	Now using THEORY for IG.
	"""
	
	def __init__(self, theta, filename):
		self.theta=theta
		adata=AnalyzedData.AnalyzedData(filename)
		adata.load()
		self.alldata=adata.alldata
	
	def choose_actions(self, subject, actioni):
		action_values={}	
		for a in world.possible_actions():
			IG=self.alldata[subject][actioni]['ActionValues'][a][0]
			PG=self.alldata[subject][actioni]['ActionValues'][a][1]
			#PGv=1-PG #invert, IG is final entropy, minimized! PG=0 -> PGv=1; PG=1 -> PGv=0
			#action_values[a]=self.theta*IG+(1-self.theta)*PGv
			action_values[a]=-self.theta*IG-(1-self.theta)*PG

		#min_value=action_values[min(action_values, key=lambda x: x[1])] #take the min value --WRONG!!!
		min_value=min(action_values.itervalues())
		#min_actions=[a for a in action_values.keys() if action_values[a]==min_value] #find ALL actions that achieve it --should be ok, cleaner below
		min_actions=[a for a,v in action_values.iteritems() if v==min_value]


		#discard repeated action choice
		if actioni>0:
			prev_action=self.alldata[subject][actioni-1]['SubjectAction']
		else:
			prev_action=()

		if len(set(min_actions)-set([prev_action])) == 0:
			del action_values[prev_action]
			min_value=min(action_values.itervalues())
			min_actions=[a for a,v in action_values.iteritems() if v==min_value]
		else:	
			min_actions=set(min_actions)-set([prev_action])

		return list(min_actions)


# 		IG_a=self.alldata[subject][actioni]['TMA']
# 		#print IG_a
# 		PM_a=self.alldata[subject][actioni]['PMA']
# 		#print PM_a

# 		choices=[IG_a, PM_a]
# 		strategy=np.random.choice(2, p=[self.theta, 1-self.theta])
# 		choice=choices[strategy]
# 		return choice






# class MixedLearner():
	
# 	""" 
# 	Player mixing IG and PM with probability theta (for IG). 
# 	Now using THEORY for IG.
# 	"""
	
# 	def __init__(self, theta):
# 		self.theta=theta
	
# 	def choose_action(self, prev_data=[]):
# 		choices=[self.IG_action(prev_data), self.PM_action(prev_data)]
# 		strategy=np.random.choice(2, p=[self.theta, 1-self.theta])
# 		choice=choices[strategy]
# 		return choice


# 	def IG_action(self, prev_data=[]):
# 		mingain=1000
# 		astars=[]
# 		for a in world.possible_actions():
# 			if len(prev_data)>0:
# 				if a==prev_data[-1].action:
# 					continue
# 			this_gain=self.expected_final_entropy(a, prev_data)
# 			if this_gain < mingain:
# 				astars=[a]
# 				mingain=this_gain
# 			elif this_gain == mingain:
# 				astars.append(a)
# 		choice=random.choice(astars)
# 		return choice

# 	def expected_final_entropy(self, action, data=None):
# 		return entropy_gains.theory_expected_final_entropy(action, data)

# 	def PM_action(self, prev_data=[]):
# 		maxprob=0
# 		astars=[]
# 		for a in world.possible_actions():
# 			if len(prev_data)>0:
# 				if a==prev_data[-1].action:
# 					continue
# 			this_prob=self.success_probability(a, prev_data)
# 			if this_prob > maxprob:
# 				astars=[a]
# 				maxprob=this_prob
# 			elif this_prob == maxprob:
# 				astars.append(a)
# 		choice=random.choice(astars)
# 		return choice


# 	def success_probability(self, action, prev_data=[]):
# 		data_no, data_yes=world.possible_data(action)
# 		p_yes=model.p_data_action(data_yes, action, prev_data)
# 		p_no=model.p_data_action(data_no, action, prev_data)
# 		return p_yes/(p_yes+p_no)



# class TabulatedMixedLearner():
	
# 	""" 
# 	Player mixing IG and PM with probability theta (for IG). 
# 	Now using THEORY for IG.
# 	"""
	
# 	def __init__(self, theta, filename):
# 		self.theta=theta
# 		adata=AnalyzedData.AnalyzedData(filename)
# 		adata.load()
# 		self.alldata=adata.alldata
	
# 	def choose_actions(self, subject, actioni, prev_data=[]):
# 		IG_a=self.alldata[subject][actioni]['TMA']
# 		#print IG_a
# 		PM_a=self.alldata[subject][actioni]['PMA']
# 		#print PM_a

# 		choices=[IG_a, PM_a]
# 		strategy=np.random.choice(2, p=[self.theta, 1-self.theta])
# 		choice=choices[strategy]
# 		return choice
