<?php 


$billets = $manager->getLastBillet();
?>

	<!--about-starts-->
	<div class="about">
		<div class="container">
			<div class="about-main">
				<div class="col-md-8 about-left">
					<div class="about-one">
						<p>Derniers chapitres</p>
						<?php foreach($billets as $billet):?>
							<h3><?php echo $billet->getTitre()?></h3>
					</div>

					<div class="about-two">
						<a href="single.php?billet_id=<?php echo $billet->getId();?>"><img src="<?php echo $billet->getImage()?>" alt="<?php echo $billet->getAlt()?> " /></a>
						<p>Posté par <a href="about.php"><?php echo $billet->getAuteur()?></a> Le
							<?php echo $billet->getDateCreation()?> <a href="#">comments(2)</a></p>
						<p>
							<?php echo $billet->getContenu()?>
						</p>
						<div class="about-btn">
							<a href="single.php?billet_id=<?php echo $billet->getId();?>">En savoir plus</a>
						</div>
						<ul>
							<li>
								<p>Share : </p>
							</li>
							<li><a href="#"><span class="fb"> </span></a></li>
							<li><a href="#"><span class="twit"> </span></a></li>
							<li><a href="#"><span class="pin"> </span></a></li>
							<li><a href="#"><span class="rss"> </span></a></li>
							<li><a href="#"><span class="drbl"> </span></a></li>
						</ul>
					</div>
					<?php endforeach;?>

						<div class="about-tre">
							<div class="a-1">
								<div class="col-md-6 abt-left">
									<a href="single.php"><img src="images/c-3.jpg" alt="" /></a>
									<h6>Find The Most</h6>
									<h3><a href="single.php">Tasty Coffee</a></h3>
									<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
									<label>May 29, 2015</label>
								</div>
								<div class="col-md-6 abt-left">
									<a href="single.php"><img src="images/c-4.jpg" alt="" /></a>
									<h6>Find The Most</h6>
									<h3><a href="single.php">Tasty Coffee</a></h3>
									<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
									<label>May 29, 2015</label>
								</div>
								<div class="clearfix"></div>
							</div>
							<div class="a-1">
								<div class="col-md-6 abt-left">
									<a href="single.php"><img src="images/c-5.jpg" alt="" /></a>
									<h6>Find The Most</h6>
									<h3><a href="single.php">Tasty Coffee</a></h3>
									<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
									<label>May 29, 2015</label>
								</div>
								<div class="col-md-6 abt-left">
									<a href="single.php"><img src="images/c-6.jpg" alt="" /></a>
									<h6>Find The Most</h6>
									<h3><a href="single.php">Tasty Coffee</a></h3>
									<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
									<label>May 29, 2015</label>
								</div>
								<div class="clearfix"></div>
							</div>
							<div class="a-1">
								<div class="col-md-6 abt-left">
									<a href="single.php"><img src="images/c-7.jpg" alt="" /></a>
									<h6>Find The Most</h6>
									<h3><a href="single.php">Tasty Coffee</a></h3>
									<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
									<label>May 29, 2015</label>
								</div>
								<div class="col-md-6 abt-left">
									<a href="single.php"><img src="images/c-8.jpg" alt="" /></a>
									<h6>Find The Most</h6>
									<h3><a href="single.php">Tasty Coffee</a></h3>
									<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
									<label>May 29, 2015</label>
								</div>
								<div class="clearfix"></div>
							</div>
						</div>
				</div>
				<div class="col-md-4 about-right heading">
					<div class="abt-1">
						<h3>A PROPOS DE L'AUTEUR</h3>
						<div class="abt-one">
							<img src="images/c-2.jpg" alt="" />
							<p>Quisque non tellus vitae mauris luctus aliquam sit amet id velit. Mauris ut dapibus nulla, a dictum neque.</p>
							<div class="a-btn">
								<a href="single.php">En savoir plus</a>
							</div>
						</div>
					</div>
					<div class="abt-2">
						<h3>LES PREMIERS CHAPITRES</h3>
						<div class="might-grid">
							<div class="grid-might">
								<a href="single.php"><img src="images/c-12.jpg" class="img-responsive" alt=""> </a>
							</div>
							<div class="might-top">
								<h4><a href="single.php">Duis consectetur gravida</a></h4>
								<p>Nullam non magna lobortis, faucibus erat eu, consequat justo. Suspendisse commodo nibh odio.</p>
							</div>
							<div class="clearfix"></div>
						</div>
						<div class="might-grid">
							<div class="grid-might">
								<a href="single.php"><img src="images/c-10.jpg" class="img-responsive" alt=""> </a>
							</div>
							<div class="might-top">
								<h4><a href="single.php">Duis consectetur gravida</a></h4>
								<p> Nullam non magna lobortis, faucibus erat eu, consequat justo. Suspendisse commodo nibh odio.</p>
							</div>
							<div class="clearfix"></div>
						</div>
						<div class="might-grid">
							<div class="grid-might">
								<a href="single.php"><img src="images/c-11.jpg" class="img-responsive" alt=""> </a>
							</div>
							<div class="might-top">
								<h4><a href="single.php">Duis consectetur gravida</a></h4>
								<p> Nullam non magna lobortis, faucibus erat eu, consequat justo. Suspendisse commodo nibh odio.</p>
							</div>
							<div class="clearfix"></div>
						</div>
					</div>


				</div>
				<div class="clearfix"></div>
			</div>
		</div>
	</div>
	<!--about-end-->